import re

from django.forms import ModelForm, TextInput, Textarea, DateInput, URLInput, Select
from main.models import Education,Project,Experience,Skill
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

class EducationForm(ModelForm):
    class Meta:
        model = Education
        fields = [
            "institution",
            "faculty_or_major",
            "degree",
            "started_at",
            "ended_at",
            "description",
        ]

        labels = {
            "institution": "Institution",
            "faculty_or_major": "Faculty / Major",
            "degree": "Degree",
            "started_at": "Start Date",
            "ended_at": "End Date",
            "description": "Description",
        }

        widgets = {
            "institution": TextInput(
                attrs={
                    "placeholder": "Universitas Indonesia",
                    "maxlength": 100,
                }
            ),
            "faculty_or_major": TextInput(
                attrs={
                    "placeholder": "Ilmu Komputer",
                    "maxlength": 100,
                }
            ),
            "degree": TextInput(
                attrs={
                    "placeholder": "S1",
                    "maxlength": 100,
                }
            ),
            "started_at": DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "ended_at": DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Describe your education experience",
                    "rows": 3,
                }
            ),
        }

    def clean_institution(self):
        institution = strip_tags(self.cleaned_data["institution"]).strip()
        if not institution:
            raise ValidationError("Institution can't contain only HTML tags.")
        return institution

    def clean_faculty_or_major(self):
        faculty_or_major = strip_tags(self.cleaned_data["faculty_or_major"]).strip()
        if not faculty_or_major:
            raise ValidationError("Faculty / Major can't contain only HTML tags.")
        return faculty_or_major

    def clean_degree(self):
        degree = strip_tags(self.cleaned_data["degree"]).strip()
        if not degree:
            raise ValidationError("Degree can't contain only HTML tags.")
        return degree

    def clean_description(self):
        return strip_tags(self.cleaned_data["description"]).strip()

        
class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "tech_stack",
            "project_url",
            "project_image_url",
        ]

        labels = {
            "title": "Nama Proyek",
            "description": "Deskripsi Proyek",
            "tech_stack": "Teknologi yang Digunakan",
            "project_url": "URL Proyek",
            "project_image_url": "URL Gambar Proyek",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Portfolio Website",
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Tell us about your project",
                    "rows": 3,
                }
            ),
            "tech_stack": TextInput(
                attrs={
                    "placeholder": "Django, Python, HTML, CSS",
                }
            ),
            "project_url": URLInput(
                attrs={
                    "placeholder": "https://github.com/kakBurhan/burhanquestv4",
                }
            ),
            "project_image_url": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
        }
        
    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Project name can't contain only HTML tags.")
        return title

    def clean_tech_stack(self):
        return strip_tags(self.cleaned_data["tech_stack"]).strip()

    def clean_description(self):
        return strip_tags(self.cleaned_data["description"]).strip()
    
class ExperienceForm(ModelForm):
    class Meta:
        model = Experience
        fields = [
            "title",
            "description",
            "category",
            "ended_at",
        ]

        labels = {
            "title": "Title",
            "description": "Description",
            "category": "Category",
            "ended_at": "End Date",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "PBP Teaching Assistant",
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Describe your experience",
                    "rows": 3,
                }
            ),
            "ended_at": DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }


class SkillForm(ModelForm):
    class Meta:
        model = Skill
        fields = ["name", "category", "icon_url"]

        labels = {
            "name": "Skill",
            "category": "Category",
            "icon_url": "Logo (optional)",
        }

        help_texts = {
            "icon_url": "Google Drive thumbnail link (a normal Drive share link also works). Leave empty to use the default image.",
        }

        widgets = {
            "name": TextInput(
                attrs={
                    "placeholder": "Django",
                    "maxlength": 50,
                }
            ),
            "category": Select(),
            "icon_url": TextInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=FILE_ID&sz=w1000",
                    "maxlength": 300,
                }
            ),
        }

    def clean_name(self):
        name = strip_tags(self.cleaned_data["name"]).strip()
        if not name:
            raise ValidationError("Skill name can't contain only HTML tags.")
        return name

    def clean_icon_url(self):
        icon_url = self.cleaned_data["icon_url"].strip()
        if not icon_url:
            return icon_url

        # A normal Drive share link (".../file/d/FILE_ID/view?usp=sharing") becomes the thumbnail URL
        share_link = re.match(r"https://drive\.google\.com/file/d/([\w-]+)", icon_url)
        if share_link:
            return f"https://drive.google.com/thumbnail?id={share_link.group(1)}&sz=w1000"

        # Only https image links, never javascript: or data: URLs
        if not icon_url.startswith("https://"):
            raise ValidationError("Use a Google Drive thumbnail link that starts with https://.")
        return icon_url

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        category = cleaned_data.get("category")

        # The same skill twice in one category is almost always a mistake
        if name and category:
            duplicates = Skill.objects.filter(name__iexact=name, category=category)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                label = dict(Skill.CATEGORY_CHOICES)[category]
                self.add_error("name", f"{name} is already listed under {label}.")
        return cleaned_data
