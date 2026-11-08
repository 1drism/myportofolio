import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.utils import timezone

from main.models import Education, Experience, Project, Skill

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "seed" / "cv_data.json"
SEED_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/1drism/myportofolio/seed_cv")
KEY_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class Section:
    name: str
    label: str
    model: type
    legacy_key: tuple
    fields: tuple
    required: tuple


SECTIONS = (
    Section(
        "skills", "skill", Skill,
        legacy_key=("name",),
        fields=("name", "category", "icon_url"),
        required=("name", "category"),
    ),
    Section(
        "projects", "project", Project,
        legacy_key=("title",),
        fields=("title", "description", "tech_stack", "project_url", "project_image_url"),
        required=("title", "description", "tech_stack"),
    ),
    Section(
        "education", "education", Education,
        legacy_key=("institution",),
        fields=("institution", "faculty_or_major", "degree", "started_at", "ended_at", "description"),
        required=("institution", "faculty_or_major", "degree", "started_at"),
    ),
    Section(
        "experience", "experience", Experience,
        legacy_key=("title", "organization"),
        fields=("title", "organization", "description", "category", "started_at", "ended_at"),
        required=("title", "description", "category", "started_at"),
    ),
)


def seed_id(section, key):
    return uuid.uuid5(SEED_NAMESPACE, f"{section.name}:{key}")


def legacy_match_key(section, values):
    return tuple(str(values[name]).strip().casefold() for name in section.legacy_key)


def legacy_row_key(section, obj):
    return legacy_match_key(section, {name: getattr(obj, name) for name in section.legacy_key})


def describe(section, values, key=None):
    text = " @ ".join(f'"{values[name]}"' for name in section.legacy_key if values[name])
    return f"{text} [{key}]" if key else text


def describe_row(section, obj):
    return describe(section, {name: getattr(obj, name) for name in section.legacy_key})


def parse_value(field, raw):
    if isinstance(field, models.DateField):
        if raw is None:
            return None
        if not isinstance(raw, str):
            raise ValidationError("must be a date string in YYYY-MM-DD format or null")
        try:
            if not DATE_PATTERN.fullmatch(raw):
                raise ValueError
            day = date.fromisoformat(raw)
        except ValueError:
            raise ValidationError(f"'{raw}' is not a valid date in YYYY-MM-DD format")
        if isinstance(field, models.DateTimeField):
            return timezone.make_aware(datetime.combine(day, time.min))
        return day
    if not isinstance(raw, str):
        raise ValidationError("must be a string")
    return raw.strip()


def clean_key(entry):
    if "key" not in entry:
        return None, "missing required field 'key'"
    key = entry["key"]
    if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key) or len(key) > 100:
        return None, f"key {key!r} must be a slug of lowercase letters, digits and hyphens, e.g. \"skill-python\""
    return key, None


def clean_entry(section, entry):
    if not isinstance(entry, dict):
        return None, None, ["must be an object"]

    errors = []
    unknown = sorted(set(entry) - set(section.fields) - {"key"})
    if unknown:
        errors.append(f"unknown field(s): {', '.join(unknown)}")

    key, key_error = clean_key(entry)
    if key_error:
        errors.append(key_error)

    values = {}
    for name in section.fields:
        field = section.model._meta.get_field(name)
        if name not in entry:
            if name in section.required:
                errors.append(f"missing required field '{name}'")
            else:
                values[name] = None if field.null else ""
            continue
        try:
            values[name] = field.clean(parse_value(field, entry[name]), None)
        except ValidationError as error:
            errors.append(f"{name}: {' '.join(error.messages)}")

    started, ended = values.get("started_at"), values.get("ended_at")
    if started and ended and ended < started:
        errors.append(f"ended_at {entry['ended_at']} is before started_at {entry['started_at']}")

    return key, values, errors


def load_seed_file(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise CommandError(f"Seed file not found: {path}")
    except json.JSONDecodeError as error:
        raise CommandError(f"{path} is not valid JSON: {error}")

    if not isinstance(data, dict):
        raise CommandError(f"{path} must contain a JSON object at the top level")

    errors = []
    unknown = sorted(set(data) - {section.name for section in SECTIONS})
    if unknown:
        errors.append(f"unknown section(s): {', '.join(unknown)}")

    cleaned = {}
    for section in SECTIONS:
        entries = data.get(section.name)
        if not isinstance(entries, list):
            errors.append(f"'{section.name}' must be a list")
            continue

        rows, seen_keys, seen_names = [], {}, {}
        for number, entry in enumerate(entries, 1):
            label = f"{section.name} #{number}"
            if isinstance(entry, dict):
                name = entry.get(section.legacy_key[0])
                if isinstance(name, str) and name.strip():
                    label += f' ("{name.strip()}")'

            key, values, entry_errors = clean_entry(section, entry)
            if entry_errors:
                errors.extend(f"{label}: {message}" for message in entry_errors)
                continue

            if key in seen_keys:
                errors.append(f"{label}: key \"{key}\" is already used by {section.name} #{seen_keys[key]}")
                continue
            name_key = legacy_match_key(section, values)
            if name_key in seen_names:
                errors.append(f"{label}: same {' + '.join(section.legacy_key)} as {section.name} #{seen_names[name_key]}")
                continue
            seen_keys[key] = seen_names[name_key] = number
            rows.append((key, values))
        cleaned[section.name] = rows

    if errors:
        raise CommandError(
            "Invalid seed file, nothing was changed:\n  " + "\n  ".join(errors)
        )
    return cleaned


def changed_fields(section, obj, values):
    return [name for name in section.fields if getattr(obj, name) != values[name]]


def plan_section(section, rows, sync, prune, start_empty):
    rows_by_id = {}
    if not start_empty:
        rows_by_id = {obj.pk: obj for obj in section.model.objects.all()}

    file_ids = {seed_id(section, key) for key, _ in rows}
    legacy = {}
    for pk, obj in rows_by_id.items():
        if pk not in file_ids:
            legacy.setdefault(legacy_row_key(section, obj), []).append(obj)

    plan = {
        "create": [], "adopt": [], "update": [], "unchanged": 0,
        "present": 0, "delete": [], "duplicates": [],
    }
    claimed = set()
    for key, values in rows:
        new_id = seed_id(section, key)
        obj = rows_by_id.get(new_id)
        if obj is not None:
            if not sync:
                plan["present"] += 1
                continue
            changed = changed_fields(section, obj, values)
            if changed:
                plan["update"].append((key, obj, values, changed))
            else:
                plan["unchanged"] += 1
            continue

        candidates = legacy.get(legacy_match_key(section, values), [])
        if candidates:
            if len(candidates) > 1:
                plan["duplicates"].append((key, values, len(candidates)))
            if not sync:
                plan["present"] += 1
                continue
            old = candidates[0]
            claimed.add(old.pk)
            plan["adopt"].append((key, old, new_id, values, changed_fields(section, old, values)))
            continue

        plan["create"].append((key, new_id, values))

    if prune:
        plan["delete"] = [
            obj for pk, obj in rows_by_id.items() if pk not in file_ids and pk not in claimed
        ]
    return plan


def adopt_row(model, old, new_id, values):
    data = {
        field.attname: getattr(old, field.attname)
        for field in model._meta.concrete_fields
        if not field.primary_key
    }
    data.update(values)
    model(pk=new_id, **data).save(force_insert=True)

    stamps = {
        field.attname: data[field.attname]
        for field in model._meta.concrete_fields
        if getattr(field, "auto_now_add", False) or getattr(field, "auto_now", False)
    }
    if stamps:
        model.objects.filter(pk=new_id).update(**stamps)

    for m2m in model._meta.many_to_many:
        through = m2m.remote_field.through
        column = through._meta.get_field(m2m.m2m_field_name()).attname
        through.objects.filter(**{column: old.pk}).update(**{column: new_id})

    old.delete()


class Command(BaseCommand):
    help = "Load the portfolio CV data (skills, projects, education, experience) from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument("--file", dest="file", default=str(DEFAULT_FILE),
                            help=f"Path to the JSON seed file (default: {DEFAULT_FILE}).")
        parser.add_argument("--sync", action="store_true",
                            help="Update existing rows with the file's values and create missing ones.")
        parser.add_argument("--prune", action="store_true",
                            help="With --sync: delete rows whose key is not in the file.")
        parser.add_argument("--if-empty", action="store_true",
                            help="Seed only when Skill, Project, Education and Experience are all empty.")
        parser.add_argument("--reset", action="store_true",
                            help="Delete ALL Skill, Project, Education and Experience rows, then seed.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Print what would happen without changing anything.")
        parser.add_argument("--confirm", action="store_true",
                            help="Required together with --prune in production.")

    def handle(self, *args, **options):
        sync, prune, reset = options["sync"], options["prune"], options["reset"]
        if_empty, dry_run = options["if_empty"], options["dry_run"]

        modes = [flag for flag, on in (("--sync", sync), ("--if-empty", if_empty), ("--reset", reset)) if on]
        if len(modes) > 1:
            raise CommandError(f"{' and '.join(modes)} cannot be used together.")
        if prune and not sync:
            raise CommandError("--prune only works together with --sync.")

        if getattr(settings, "PRODUCTION", False):
            if os.environ.get("SEED_CV_ON_DEPLOY", "").strip().lower() != "true":
                raise CommandError("Refusing to run in production: set SEED_CV_ON_DEPLOY=true to allow seed_cv.")
            if reset:
                raise CommandError("--reset is not allowed in production.")
            if prune and not options["confirm"]:
                raise CommandError("--prune deletes rows in production; pass --confirm as well to allow it.")

        data = load_seed_file(options["file"])

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run: nothing will be changed."))

        if if_empty and any(section.model.objects.exists() for section in SECTIONS):
            self.stdout.write("Data already present, skipping")
            return

        plans = [
            (section, plan_section(section, data[section.name], sync, prune, start_empty=reset))
            for section in SECTIONS
        ]

        reset_counts = None
        if reset:
            reset_counts = {section.name: section.model.objects.count() for section in SECTIONS}
        if not dry_run:
            with transaction.atomic():
                if reset:
                    for section in SECTIONS:
                        section.model.objects.all().delete()
                for section, plan in plans:
                    for obj in plan["delete"]:
                        obj.delete()
                    for key, old, new_id, values, changed in plan["adopt"]:
                        adopt_row(section.model, old, new_id, values)
                    for key, obj, values, changed in plan["update"]:
                        for name in changed:
                            setattr(obj, name, values[name])
                        obj.save(update_fields=changed)
                    for key, new_id, values in plan["create"]:
                        section.model.objects.create(pk=new_id, **values)

        self.report(plans, sync, prune, dry_run, reset_counts)

    def report(self, plans, sync, prune, dry_run, reset_counts):
        def verb(done, planned):
            return planned if dry_run else done

        if reset_counts is not None:
            removed = ", ".join(f"{count} {name}" for name, count in reset_counts.items())
            self.stdout.write(f"{verb('Deleted', 'Would delete')} all existing rows: {removed}")

        for section, plan in plans:
            parts = [f"{len(plan['create'])} {verb('created', 'to create')}"]
            if sync:
                parts.append(f"{len(plan['adopt'])} {verb('adopted', 'to adopt')}")
                parts.append(f"{len(plan['update'])} {verb('updated', 'to update')}")
                parts.append(f"{plan['unchanged']} unchanged")
            elif reset_counts is None:
                parts.append(f"{plan['present']} already present")
            if prune:
                parts.append(f"{len(plan['delete'])} {verb('deleted', 'to delete')}")
            self.stdout.write(f"{section.name}: {', '.join(parts)}")

            for key, new_id, values in plan["create"]:
                self.stdout.write(f"  + {verb('created', 'would create')} {section.label} {describe(section, values, key)}")
            for key, old, new_id, values, changed in plan["adopt"]:
                detail = f", updated: {', '.join(changed)}" if changed else ""
                self.stdout.write(
                    f"  = {verb('adopted', 'would adopt')} {section.label} {describe(section, values, key)}"
                    f" (existing row, id {old.pk} -> {new_id}{detail})"
                )
            for key, obj, values, changed in plan["update"]:
                self.stdout.write(
                    f"  ~ {verb('updated', 'would update')} {section.label} {describe(section, values, key)}: {', '.join(changed)}"
                )
            for obj in plan["delete"]:
                self.stdout.write(self.style.WARNING(
                    f"  - {verb('deleted', 'would delete')} {section.label} {describe_row(section, obj)}"
                ))
            for key, values, count in plan["duplicates"]:
                self.stdout.write(self.style.WARNING(
                    f"  ! {count} existing {section.name} rows match {describe(section, values, key)}; "
                    "only one is used, the others stay until you run --sync --prune"
                ))

        self.stdout.write(self.style.SUCCESS("Dry run finished, nothing was changed." if dry_run else "Done."))
