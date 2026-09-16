from django.forms import ModelForm, TextInput, Textarea, DateInput, URLInput
from main.models import Education,Project

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