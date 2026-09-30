from main.models import Experience,Education,Project
from main.forms import EducationForm,ProjectForm,ExperienceForm

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

import datetime

# Helper function to check is the user editor
def is_editor(user):
    return user.groups.filter(name='Editor').exists()
    
    
def show_main(request):
    last_login = request.COOKIES.get('last_login', 'No active login session / Cookie not found')
    
    context = {
        "name": "Muhamad Idris Kamal",
        "npm": "2506637073",
        "study_program": "S1 Ilmu Komputer KKI",
        "bio": (
            "Hi, I'm Idris! I'm a CS student at Universitas Indonesia (Fasilkom UI) who is deeply interested in the world of cybersecurity. I love learning about how systems and software work under the hood, and I'm eager to learn more about how to keep those systems secure. Outside of tech, I'm a fan of Reality Club and will always be Burhan lover #1 (definitely not a hater)"
        ),
        "last_login": last_login,
    }
    return render(request, "index.html", context)

def show_experience(request):
    context = {
        "name": "Idris",
        "experience_list": Experience.objects.all(),
        "is_editor": is_editor(request.user),
    }
    return render(request, "experience.html", context)

@login_required(login_url="/login/")
def create_education(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
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

@login_required(login_url="/login/")
def create_project(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project added!")
        return redirect("main:show_projects")

    context = {
        "name": "Idris",
        "form": form,
    }
    return render(request, "project_form.html", context)

@login_required(login_url="/login/")
def create_experience(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience added!")
        return redirect("main:show_experience")

    context = {"name": "Idris", "form": form}
    return render(request, "experience_form.html", context)

def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.prefetch_related('starred_by').all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    # Manually build the JSON data so we can add the Star logic
    data = []
    for project in projects:
        starred_users = project.starred_by.all()
        is_starred = request.user in starred_users if request.user.is_authenticated else False
        starred_by_names = ", ".join([u.username for u in starred_users])

        data.append({
            "pk": str(project.id),
            "fields": {
                "title": project.title,
                "description": project.description,
                "tech_stack": project.tech_stack,
                "project_url": project.project_url,
                "project_image_url": project.project_image_url,
                "star_count": starred_users.count(),
                "is_starred": is_starred,
                "starred_by_names": starred_by_names,
            }
        })

    return JsonResponse(data, safe=False)


def get_education_json(request):
    institution_query = request.GET.get("institution", "").strip()
    education_list = Education.objects.prefetch_related('starred_by').all()

    if institution_query:
        education_list = education_list.filter(institution__icontains=institution_query)

    # Manually build the JSON data so we can add the Star logic
    data = []
    for education in education_list:
        starred_users = education.starred_by.all()
        is_starred = request.user in starred_users if request.user.is_authenticated else False
        starred_by_names = ", ".join([u.username for u in starred_users])

        data.append({
            "pk": str(education.id),
            "fields": {
                "institution": education.institution,
                "faculty_or_major": education.faculty_or_major,
                "degree": education.degree,
                "description": education.description,
                "started_at": education.started_at.isoformat(),
                "ended_at": education.ended_at.isoformat() if education.ended_at else None,
                "is_ongoing": education.is_ongoing,
                "star_count": starred_users.count(),
                "is_starred": is_starred,
                "starred_by_names": starred_by_names,
            }
        })

    return JsonResponse(data, safe=False)

def show_projects(request):
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": "Idris",
        "title_query": title_query,
        "form": ProjectForm(),
        "is_editor": is_editor(request.user),
    }
    return render(request, "project.html", context)

def show_education(request):
    institution_query = request.GET.get("institution", "").strip()

    context = {
        "name": "Idris",
        "institution_query": institution_query,
        "form": EducationForm(),
        "is_editor": is_editor(request.user),
    }
    return render(request, "education.html", context)

@login_required(login_url="/login/")
def delete_project(request, project_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        project.delete()

        # AJAX request: the page shows its own toast, so just confirm with JSON
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"message": "Project deleted successfully."})

        messages.success(request, "Project deleted!")
        return redirect("main:show_projects")

    return redirect("main:show_projects")

@login_required(login_url="/login/")
def delete_education(request, education_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    education = get_object_or_404(Education, pk=education_id)

    if request.method == "POST":
        education.delete()

        # AJAX request: the page shows its own toast, so just confirm with JSON
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"message": "Education deleted successfully."})

        messages.success(request, "Education deleted!")
        return redirect("main:show_education")

    return redirect("main:show_education")

@login_required(login_url="/login/")
def delete_experience(request, experience_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST":
        experience.delete()
        messages.success(request, "Experience deleted!")
        return redirect("main:show_experience")

    return redirect("main:show_experience")

@login_required(login_url="/login/")
def edit_education(request, education_id):
    if not (request.user.is_superuser or is_editor(request.user)):
        raise PermissionDenied
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

@login_required(login_url="/login/")
def edit_project(request, project_id):
    if not (request.user.is_superuser or is_editor(request.user)):
        raise PermissionDenied
    
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

@login_required(login_url="/login/")
def edit_experience(request, experience_id):
    if not (request.user.is_superuser or is_editor(request.user)):
        raise PermissionDenied
    
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience updated!")
        return redirect("main:show_experience")

    context = { "name": "Idris",
               "form": form,
               "experience": experience,
    }
    return render(request, "experience_form.html", context)


# Login thingy below
def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created successfully. Please log in.")
        return redirect("main:login")

    context = {
        "name": "Idris",
        "form": form,
    }
    return render(request, "register.html", context)

def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": "Idris",
        "form": form,
    }
    return render(request, "login.html", context)

def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response

# Star button
@login_required(login_url="/login/")
def toggle_project_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        if request.user in project.starred_by.all():
            project.starred_by.remove(request.user)
        else:
            project.starred_by.add(request.user)

    # Ajax send back new star state instead of redirecting
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        starred_users = project.starred_by.all()
        return JsonResponse({
            "is_starred": request.user in starred_users,
            "star_count": starred_users.count(),
            "starred_by_names": ", ".join([u.username for u in starred_users]),
        })

    return redirect("main:show_projects")

@login_required(login_url="/login/")
def toggle_education_star(request, education_id):
    education = get_object_or_404(Education, pk=education_id)

    if request.method == "POST":
        if request.user in education.starred_by.all():
            education.starred_by.remove(request.user)
        else:
            education.starred_by.add(request.user)

    # AJAX request: send back the new star state instead of redirecting
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        starred_users = education.starred_by.all()
        return JsonResponse({
            "is_starred": request.user in starred_users,
            "star_count": starred_users.count(),
            "starred_by_names": ", ".join([u.username for u in starred_users]),
        })

    return redirect("main:show_education")


@require_POST
def create_project_ajax(request):
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Only the portfolio owner can add projects."},
            status=403,
        )

    form = ProjectForm(request.POST)
    if form.is_valid():
        project = form.save()
        return JsonResponse(
            {"message": "Project added successfully.", "pk": str(project.id)},
            status=201,
        )

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)


@require_POST
def edit_project_ajax(request, project_id):
    # Superuser and Editor can edit (Assignment 4 roles); JSON 403 instead of a login redirect
    if not (request.user.is_superuser or is_editor(request.user)):
        return JsonResponse(
            {"message": "Only the portfolio owner or an editor can edit projects."},
            status=403,
        )

    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return JsonResponse({"message": "This project no longer exists."}, status=404)

    form = ProjectForm(request.POST, instance=project)
    if form.is_valid():
        form.save()
        return JsonResponse({"message": "Project updated successfully.", "pk": str(project.id)})

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)


@require_POST
def create_education_ajax(request):
    # No @login_required: it would redirect fetch to the login page (200 HTML) instead of a JSON 403
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Only the portfolio owner can add education."},
            status=403,
        )

    form = EducationForm(request.POST)
    if form.is_valid():
        education = form.save()
        return JsonResponse(
            {"message": "Education added successfully.", "pk": str(education.id)},
            status=201,
        )

    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
