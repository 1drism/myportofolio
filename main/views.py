from django.shortcuts import render

from main.models import Experience,Education,Project
from main.forms import EducationForm,ProjectForm,ExperienceForm

from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

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

def create_education(request):
    form = EducationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Education added!")
        return redirect("main:show_education")

    context = {
        "name": "Idris",
        "form": form,
    }
    return render(request, "education_form.html", context)

def create_project(request):
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    context = {
        "name": "Idris",
        "form": form,
    }
    return render(request, "project_form.html", context)

def create_experience(request):
    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience added!")
        return redirect("main:show_experience")

    context = {"name": "Idris", "form": form}
    return render(request, "experience_form.html", context)

def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    projects_json = serializers.serialize("json", projects)
    return HttpResponse(projects_json, content_type="application/json")


def get_education_json(request):
    institution_query = request.GET.get("institution", "").strip()
    education = Education.objects.all()

    if institution_query:
        education = education.filter(institution__icontains=institution_query)

    education_json = serializers.serialize("json", education)
    return HttpResponse(education_json, content_type="application/json")

def show_projects(request):
    json_response = get_projects_json(request)

    projects = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    projects = [project.object for project in projects]
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": "Idris",
        "project_list": projects,
        "title_query": title_query,
    }
    return render(request, "project.html", context)

def show_education(request):
    json_response = get_education_json(request)

    education_list = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    education_list = [item.object for item in education_list]
    institution_query = request.GET.get("institution", "").strip()

    context = {
        "name": "Idris",
        "education_list": education_list,
        "institution_query": institution_query,
    }
    return render(request, "education.html", context)

def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project deleted!")
        return redirect("main:show_projects")

    return redirect("main:show_projects")


def delete_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)

    if request.method == "POST":
        education.delete()
        messages.success(request, "Education deleted!")
        return redirect("main:show_education")

    return redirect("main:show_education")

def delete_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        experience.delete()
        messages.success(request, "Experience deleted!")
        return redirect("main:show_experience")

    return redirect("main:show_experience")

def edit_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)
    form = EducationForm(request.POST or None, instance=education)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Education updated!")
        return redirect("main:show_education")

    context = {
        "name": "Idris",
        "form": form,
        "education": education,
    }
    return render(request, "education_form.html", context)

def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = ProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project updated!")
        return redirect("main:show_projects")

    context = {
        "name": "Idris",
        "form": form,
        "project": project,
    }
    return render(request, "project_form.html", context)

def edit_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience updated!")
        return redirect("main:show_experience")

    context = {"name": "Idris", "form": form, "experience": experience}
    return render(request, "experience_form.html", context)