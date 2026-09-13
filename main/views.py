from django.shortcuts import render

from main.models import Experience
from main.models import Education

def show_main(request):
    context = {
        "name": "Muhamad Idris Kamal",
        "npm": "2506637073",
        "study_program": "S1 Ilmu Komputer KKI",
        "bio": (
            "Hi, I'm Idris! I'm a CS student at Universitas Indonesia (Fasilkom UI) who is deeply interested in the world of cybersecurity. I love learning about how systems and software work under the hood, and I'm eager to learn more about how to keep those systems secure. Outside of tech, I'm a fan of Reality Club and will always be Burhan lover #1 (definitely not a hater)"
        ),
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Idris",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

def show_education(request):
    context = {
        "name": "Idris",
        "education_list": Education.objects.all(),
    }
    return render(request, "education.html", context)