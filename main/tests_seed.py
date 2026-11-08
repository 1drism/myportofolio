import copy
import json
import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from main.management.commands.seed_cv import DEFAULT_FILE
from main.models import Education, Experience, Project, Skill

FULL_COUNTS = (11, 2, 2, 7)


class SeedCvTestBase(TestCase):
    def setUp(self):
        self.data = json.loads(DEFAULT_FILE.read_text(encoding="utf-8"))
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def write(self, data):
        path = self.tmp / "cv_data.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def seed(self, *args, **kwargs):
        out = StringIO()
        call_command("seed_cv", *args, stdout=out, **kwargs)
        return out.getvalue()

    def counts(self):
        return (
            Skill.objects.count(),
            Project.objects.count(),
            Education.objects.count(),
            Experience.objects.count(),
        )


class SeedCvCommandTest(SeedCvTestBase):
    def test_reset_gives_exact_counts(self):
        Skill.objects.create(name="Rust", category="technical")
        Project.objects.create(title="Old project", description="x", tech_stack="x")

        self.seed("--reset")

        self.assertEqual(self.counts(), FULL_COUNTS)
        self.assertFalse(Skill.objects.filter(name="Rust").exists())
        self.assertFalse(Project.objects.filter(title="Old project").exists())

    def test_experience_dates_are_timezone_aware(self):
        self.seed()

        mentor = Experience.objects.get(title="Mentor, Dasar-Dasar Pemrograman 0")
        self.assertTrue(timezone.is_aware(mentor.started_at))
        self.assertEqual(timezone.localdate(mentor.started_at).isoformat(), "2026-07-01")
        self.assertEqual(timezone.localdate(mentor.ended_at).isoformat(), "2026-08-31")
        ongoing = Experience.objects.get(title="Sports Department Staff")
        self.assertIsNone(ongoing.ended_at)

    def test_running_twice_creates_no_duplicates(self):
        self.seed()
        out = self.seed()

        self.assertEqual(self.counts(), FULL_COUNTS)
        self.assertIn("skills: 0 created, 11 already present", out)

        self.seed("--sync")
        self.assertEqual(self.counts(), FULL_COUNTS)

    def test_existing_rows_match_case_insensitively(self):
        Skill.objects.create(name="python", category="technical")

        self.seed()

        self.assertEqual(Skill.objects.filter(name__iexact="python").count(), 1)
        self.assertEqual(Skill.objects.count(), 11)

    def test_sync_updates_adds_and_keeps_stars(self):
        self.seed()
        user = User.objects.create_user(username="visitor", password="pass12345")
        project = Project.objects.get(title="urFunFarming")
        project.starred_by.add(user)
        education = Education.objects.get(institution="Universitas Indonesia")
        education.starred_by.add(user)

        data = copy.deepcopy(self.data)
        data["projects"][1]["description"] = "Updated description."
        data["education"][0]["description"] = "International undergraduate program."
        data["skills"].append({"key": "skill-rust", "name": "Rust", "category": "technical", "icon_url": ""})

        out = self.seed("--sync", file=self.write(data))

        project.refresh_from_db()
        education.refresh_from_db()
        self.assertEqual(project.description, "Updated description.")
        self.assertEqual(education.description, "International undergraduate program.")
        self.assertIn(user, project.starred_by.all())
        self.assertIn(user, education.starred_by.all())
        self.assertTrue(Skill.objects.filter(name="Rust").exists())
        self.assertEqual(self.counts(), (12, 2, 2, 7))
        self.assertIn("skills: 1 created, 0 adopted, 0 updated, 11 unchanged", out)
        self.assertIn("projects: 0 created, 0 adopted, 1 updated, 1 unchanged", out)

    def test_renamed_title_updates_same_row(self):
        self.seed()
        user = User.objects.create_user(username="visitor", password="pass12345")
        project = Project.objects.get(title="urFunFarming")
        project.starred_by.add(user)
        alkafest = Experience.objects.get(organization="ALKAFEST")

        data = copy.deepcopy(self.data)
        data["projects"][1]["title"] = "urFunFarming Marketplace"
        data["experience"][6]["title"] = "Vice Head of E-Sport Division"
        out = self.seed("--sync", file=self.write(data))

        self.assertEqual(self.counts(), FULL_COUNTS)
        renamed_project = Project.objects.get(title="urFunFarming Marketplace")
        self.assertEqual(renamed_project.pk, project.pk)
        self.assertIn(user, renamed_project.starred_by.all())
        self.assertFalse(Project.objects.filter(title="urFunFarming").exists())
        renamed_experience = Experience.objects.get(organization="ALKAFEST")
        self.assertEqual(renamed_experience.pk, alkafest.pk)
        self.assertEqual(renamed_experience.title, "Vice Head of E-Sport Division")
        self.assertIn("projects: 0 created, 0 adopted, 1 updated, 1 unchanged", out)

    def test_sync_adopts_rows_created_before_keys(self):
        user = User.objects.create_user(username="visitor", password="pass12345")
        old_skill = Skill.objects.create(name="python", category="technical")
        old_project = Project.objects.create(title="urFunFarming", description="Old.", tech_stack="Django")
        old_project.starred_by.add(user)
        old_experience = Experience.objects.create(
            title="Vice Head of E-Sport Division & Sponsorship Staff",
            organization="ALKAFEST",
            description="Old.",
            category="volunteer",
        )

        out = self.seed("--sync")

        self.assertEqual(self.counts(), FULL_COUNTS)
        self.assertIn("skills: 10 created, 1 adopted", out)
        self.assertIn("projects: 1 created, 1 adopted", out)
        self.assertIn("experience: 6 created, 1 adopted", out)

        skill = Skill.objects.get(name="Python")
        self.assertNotEqual(skill.pk, old_skill.pk)
        self.assertEqual(skill.created_at, old_skill.created_at)
        project = Project.objects.get(title="urFunFarming")
        self.assertNotEqual(project.pk, old_project.pk)
        self.assertEqual(project.description, self.data["projects"][1]["description"])
        self.assertIn(user, project.starred_by.all())
        self.assertFalse(Project.objects.filter(pk=old_project.pk).exists())
        self.assertFalse(Experience.objects.filter(pk=old_experience.pk).exists())

        data = copy.deepcopy(self.data)
        data["projects"][1]["title"] = "urFunFarming Marketplace"
        out = self.seed("--sync", file=self.write(data))
        self.assertIn("projects: 0 created, 0 adopted, 1 updated, 1 unchanged", out)
        self.assertEqual(Project.objects.get(title="urFunFarming Marketplace").pk, project.pk)

    def test_default_mode_does_not_adopt(self):
        old_project = Project.objects.create(title="urFunFarming", description="Old.", tech_stack="Django")

        out = self.seed()

        self.assertIn("projects: 1 created, 1 already present", out)
        self.assertEqual(Project.objects.count(), 2)
        old_project.refresh_from_db()
        self.assertEqual(old_project.description, "Old.")

    def test_sync_prune_removes_only_missing_entries(self):
        self.seed()
        data = copy.deepcopy(self.data)
        data["skills"] = [s for s in data["skills"] if s["name"] != "Java"]
        data["experience"] = [e for e in data["experience"] if e["title"] != "Operational Staff"]

        out = self.seed("--sync", "--prune", file=self.write(data))

        self.assertEqual(self.counts(), (10, 2, 2, 6))
        self.assertFalse(Skill.objects.filter(name="Java").exists())
        self.assertFalse(Experience.objects.filter(title="Operational Staff").exists())
        self.assertTrue(Skill.objects.filter(name="Python").exists())
        self.assertIn('deleted skill "Java"', out)
        self.assertIn('deleted experience "Operational Staff" @ "Open House Fasilkom UI"', out)

    def test_prune_without_sync_is_rejected(self):
        with self.assertRaises(CommandError):
            self.seed("--prune")

    def test_modes_cannot_be_combined(self):
        with self.assertRaises(CommandError):
            self.seed("--sync", "--reset")
        self.assertEqual(self.counts(), (0, 0, 0, 0))

    def test_if_empty_skips_when_data_exists(self):
        Skill.objects.create(name="Rust", category="technical")

        out = self.seed("--if-empty")

        self.assertIn("Data already present, skipping", out)
        self.assertEqual(self.counts(), (1, 0, 0, 0))

    def test_if_empty_seeds_empty_database(self):
        self.seed("--if-empty")

        self.assertEqual(self.counts(), FULL_COUNTS)

    def test_invalid_entry_changes_nothing(self):
        self.seed()
        Skill.objects.create(name="Rust", category="technical")
        before = self.counts()

        cases = [
            ("category", "experience", 3, "category", "hobby"),
            ("started_at", "education", 0, "started_at", "2025/08/01"),
            ("'2025-5-29' is not a valid date", "experience", 6, "ended_at", "2025-5-29"),
            ("is before started_at", "experience", 0, "ended_at", "2020-01-01"),
            ("title", "projects", 0, "title", ""),
            ("project_url", "projects", 1, "project_url", "not a url"),
            ("must be a slug", "skills", 0, "key", "Skill Python"),
        ]
        for reason, section, index, field, value in cases:
            for mode in ("--sync", "--reset"):
                with self.subTest(reason=reason, mode=mode):
                    data = copy.deepcopy(self.data)
                    data["projects"][0]["description"] = "Should not be saved."
                    data[section][index][field] = value

                    with self.assertRaises(CommandError) as raised:
                        self.seed(mode, file=self.write(data))

                    self.assertEqual(raised.exception.returncode, 1)
                    self.assertIn(f"{section} #{index + 1}", str(raised.exception))
                    self.assertIn(reason, str(raised.exception))
                    self.assertEqual(self.counts(), before)
                    self.assertNotEqual(
                        Project.objects.get(title="Personal Portfolio Website").description,
                        "Should not be saved.",
                    )

    def test_missing_field_and_duplicate_key_are_rejected(self):
        data = copy.deepcopy(self.data)
        del data["skills"][0]["category"]
        del data["projects"][0]["key"]
        data["skills"].append({"key": "skill-java-2", "name": "java", "category": "technical", "icon_url": ""})
        data["skills"].append({"key": "skill-git", "name": "GitHub", "category": "software", "icon_url": ""})

        with self.assertRaises(CommandError) as raised:
            self.seed(file=self.write(data))

        message = str(raised.exception)
        self.assertIn("missing required field 'category'", message)
        self.assertIn("projects #1 (\"Personal Portfolio Website\"): missing required field 'key'", message)
        self.assertIn("same name as skills #2", message)
        self.assertIn('key "skill-git" is already used by skills #5', message)
        self.assertEqual(self.counts(), (0, 0, 0, 0))

    def test_dry_run_changes_nothing(self):
        Skill.objects.create(name="Rust", category="technical")

        out = self.seed("--reset", "--dry-run")
        self.assertIn("Would delete all existing rows: 1 skills", out)
        self.assertEqual(self.counts(), (1, 0, 0, 0))

        self.seed("--dry-run")
        self.assertEqual(self.counts(), (1, 0, 0, 0))

        self.seed()
        data = copy.deepcopy(self.data)
        data["projects"][0]["description"] = "Changed."
        out = self.seed("--sync", "--prune", "--dry-run", file=self.write(data))
        self.assertIn('would delete skill "Rust"', out)
        self.assertIn("would update project", out)
        self.assertTrue(Skill.objects.filter(name="Rust").exists())
        self.assertNotEqual(Project.objects.get(title="Personal Portfolio Website").description, "Changed.")


@override_settings(PRODUCTION=True)
class SeedCvProductionTest(SeedCvTestBase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("SEED_CV_ON_DEPLOY", None)

    def test_refuses_without_env_var(self):
        for value in (None, "false", "1"):
            with self.subTest(value=value):
                if value is not None:
                    os.environ["SEED_CV_ON_DEPLOY"] = value
                with self.assertRaisesMessage(CommandError, "SEED_CV_ON_DEPLOY"):
                    self.seed("--sync")
                self.assertEqual(self.counts(), (0, 0, 0, 0))

    def test_runs_with_env_var(self):
        os.environ["SEED_CV_ON_DEPLOY"] = "true"

        self.seed("--sync")

        self.assertEqual(self.counts(), FULL_COUNTS)

    def test_reset_always_refuses(self):
        os.environ["SEED_CV_ON_DEPLOY"] = "true"
        Skill.objects.create(name="Rust", category="technical")

        for args in (("--reset",), ("--reset", "--confirm"), ("--reset", "--dry-run")):
            with self.subTest(args=args):
                with self.assertRaisesMessage(CommandError, "--reset"):
                    self.seed(*args)
                self.assertEqual(self.counts(), (1, 0, 0, 0))

    def test_prune_needs_confirm(self):
        os.environ["SEED_CV_ON_DEPLOY"] = "true"
        Skill.objects.create(name="Rust", category="technical")

        with self.assertRaisesMessage(CommandError, "--confirm"):
            self.seed("--sync", "--prune")
        self.assertTrue(Skill.objects.filter(name="Rust").exists())

        self.seed("--sync", "--prune", "--confirm")
        self.assertFalse(Skill.objects.filter(name="Rust").exists())
        self.assertEqual(self.counts(), FULL_COUNTS)


class ExperienceOrderTest(SeedCvTestBase):
    EXPECTED = [
        "Sports Department Staff",
        "Teaching Assistant, Foundations of Programming 1",
        "Mentor, Dasar-Dasar Pemrograman 0",
        "Event Decoration Staff",
        "Operational Staff",
        "Sports Department Trainee",
        "Vice Head of E-Sport Division & Sponsorship Staff",
    ]

    def page_titles(self):
        response = self.client.get(reverse("main:show_experience"))
        return [experience.title for experience in response.context["experience_list"]]

    def test_same_start_date_has_stable_order(self):
        self.seed()
        self.assertEqual(self.page_titles(), self.EXPECTED)

        data = copy.deepcopy(self.data)
        data["experience"].reverse()
        self.seed("--reset", file=self.write(data))

        self.assertEqual(self.page_titles(), self.EXPECTED)
        self.assertEqual(self.page_titles(), self.EXPECTED)
