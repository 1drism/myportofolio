from django.urls import path

from main.views import (show_main, show_experience,show_education,
                        create_education, show_projects,create_project,
                        get_education_json,get_projects_json,delete_project,
                        delete_education,edit_education,edit_project,
                        create_experience,edit_experience,delete_experience,
                        register,login_user,logout_user)

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("education/", show_education, name="show_education"),
    path("education/add/", create_education, name="create_education"),
    path("projects/", show_projects, name="show_projects"),
    path("projects/add/", create_project, name="create_project"),
    path("api/projects/", get_projects_json, name="get_projects_json"),
    path("api/education/", get_education_json, name="get_education_json"),
    path("projects/<uuid:project_id>/delete/", delete_project, name="delete_project"),
    path("education/<uuid:education_id>/delete/", delete_education, name="delete_education"),
    path("education/<uuid:education_id>/edit/", edit_education, name="edit_education"),
    path("projects/<uuid:project_id>/edit/", edit_project, name="edit_project"),
    path("experience/add/", create_experience, name="create_experience"),
    path("experience/<uuid:experience_id>/edit/", edit_experience, name="edit_experience"),
    path("experience/<uuid:experience_id>/delete/", delete_experience, name="delete_experience"),
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
]