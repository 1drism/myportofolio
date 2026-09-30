from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience,Education,Project

class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="PBP Teaching Assistant",
            description="Help students understand web development.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/a-page-that-does-not-exist/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "PBP Teaching Assistant")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Ongoing")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "No experience has been added yet.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Completed")
        self.assertNotContains(response, "Ongoing")
        
class EducationTest(TestCase):
    def setUp(self):
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            faculty_or_major="Ilmu Komputer",
            degree="S1",
            started_at="2025-08-01",
        )
    def test_education_url_is_acessible(self):
            response = self.client.get(reverse("main:show_education"))
    
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "education.html")
            self.assertContains(response, f'href="{reverse("main:show_experience")}"')
            self.assertContains(response, f'href="{reverse("main:show_main")}"')
            
    def test_education_page_is_skeleton(self):
        # The page only renders the skeleton, JavaScript fetches the data afterwards
        Education.objects.create(
            institution="Skeleton Check Institute",
            faculty_or_major="Testing",
            degree="S3",
            started_at="2020-01-01",
        )
        response = self.client.get(reverse("main:show_education"))

        self.assertContains(response, 'id="grid"')
        self.assertContains(response, 'id="loading"')
        self.assertContains(response, 'id="error"')
        self.assertContains(response, reverse("main:get_education_json"))
        self.assertNotContains(response, "Skeleton Check Institute")

    def test_education_data_in_json(self):
        response = self.client.get(reverse("main:get_education_json"))
        fields = response.json()[0]["fields"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(fields["institution"], self.education.institution)
        self.assertEqual(fields["degree"], self.education.degree)
        self.assertEqual(fields["faculty_or_major"], self.education.faculty_or_major)
        self.assertEqual(fields["started_at"], "2025-08-01")
        self.assertTrue(fields["is_ongoing"])

    def test_empty_education_page(self):
        Education.objects.all().delete()
        page = self.client.get(reverse("main:show_education"))
        response = self.client.get(reverse("main:get_education_json"))

        self.assertContains(page, "No education has been added or found yet.")
        self.assertEqual(response.json(), [])

    def test_education_search(self):
        Education.objects.create(
            institution="SMA Negeri 8",
            faculty_or_major="IPA",
            degree="SMA",
            started_at="2022-07-01",
        )
        response = self.client.get(reverse("main:get_education_json"), {"institution": "universitas"})
        institutions = [item["fields"]["institution"] for item in response.json()]

        self.assertEqual(institutions, ["Universitas Indonesia"])


class AjaxTestBase(TestCase):
    """Creates one user for every role from Assignment 4."""

    def setUp(self):
        # No passwords: force_login doesn't need them, and hashing makes the tests slow
        self.owner = User.objects.create_user("owner", is_superuser=True, is_staff=True)
        self.editor = User.objects.create_user("editor")
        self.editor.groups.add(Group.objects.create(name="Editor"))
        self.visitor = User.objects.create_user("visitor")

    def login(self, user):
        self.client.force_login(user)


class EducationAjaxTest(AjaxTestBase):
    def setUp(self):
        super().setUp()
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            faculty_or_major="Ilmu Komputer",
            degree="S1",
            started_at="2025-08-01",
        )
        self.valid_data = {
            "institution": "Universitas Gadjah Mada",
            "faculty_or_major": "Teknik",
            "degree": "S2",
            "started_at": "2027-08-01",
            "description": "",
        }
        self.edit_url = reverse("main:edit_education_ajax", args=[self.education.id])

    def test_star_info_in_json(self):
        self.education.starred_by.add(self.visitor)

        guest_fields = self.client.get(reverse("main:get_education_json")).json()[0]["fields"]
        self.login(self.visitor)
        visitor_fields = self.client.get(reverse("main:get_education_json")).json()[0]["fields"]

        self.assertEqual(guest_fields["star_count"], 1)
        self.assertFalse(guest_fields["is_starred"])
        self.assertTrue(visitor_fields["is_starred"])
        self.assertEqual(visitor_fields["starred_by_names"], "visitor")

    def test_create_as_owner(self):
        self.login(self.owner)
        response = self.client.post(reverse("main:create_education_ajax"), self.valid_data)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Education.objects.filter(institution="Universitas Gadjah Mada").exists())

    def test_create_forbidden_for_other_roles(self):
        for user in [None, self.visitor, self.editor]:
            self.client.logout()
            if user:
                self.login(user)
            response = self.client.post(reverse("main:create_education_ajax"), self.valid_data)
            self.assertEqual(response.status_code, 403)

        self.assertEqual(Education.objects.count(), 1)

    def test_create_invalid_returns_errors(self):
        self.login(self.owner)
        response = self.client.post(
            reverse("main:create_education_ajax"),
            {**self.valid_data, "institution": "<img src=x onerror=alert(1)>", "degree": ""},
        )
        errors = response.json()["errors"]

        self.assertEqual(response.status_code, 400)
        self.assertIn("institution", errors)
        self.assertIn("degree", errors)

    def test_create_strips_html_tags(self):
        self.login(self.owner)
        self.client.post(
            reverse("main:create_education_ajax"),
            {**self.valid_data, "institution": "<b>Universitas</b> Gadjah Mada", "description": "<i>hi</i>"},
        )
        education = Education.objects.get(degree="S2")

        self.assertEqual(education.institution, "Universitas Gadjah Mada")
        self.assertEqual(education.description, "hi")

    def test_create_requires_post(self):
        self.login(self.owner)
        response = self.client.get(reverse("main:create_education_ajax"))

        self.assertEqual(response.status_code, 405)

    def test_create_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)
        response = csrf_client.post(reverse("main:create_education_ajax"), self.valid_data)

        self.assertEqual(response.status_code, 403)

    def test_edit_as_owner_and_editor(self):
        for user in [self.owner, self.editor]:
            self.login(user)
            response = self.client.post(self.edit_url, {**self.valid_data, "institution": f"Edited by {user}"})
            self.education.refresh_from_db()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.education.institution, f"Edited by {user}")

    def test_edit_forbidden_for_visitor_and_guest(self):
        response = self.client.post(self.edit_url, self.valid_data)
        self.assertEqual(response.status_code, 403)

        self.login(self.visitor)
        response = self.client.post(self.edit_url, self.valid_data)
        self.assertEqual(response.status_code, 403)

        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Universitas Indonesia")

    def test_edit_missing_returns_404(self):
        self.login(self.owner)
        response = self.client.post(
            reverse("main:edit_education_ajax", args=["00000000-0000-0000-0000-000000000000"]),
            self.valid_data,
        )

        self.assertEqual(response.status_code, 404)

    def test_star_toggle_ajax(self):
        self.login(self.visitor)
        url = reverse("main:toggle_education_star", args=[self.education.id])

        starred = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
        unstarred = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()

        self.assertTrue(starred["is_starred"])
        self.assertEqual(starred["star_count"], 1)
        self.assertFalse(unstarred["is_starred"])
        self.assertEqual(unstarred["star_count"], 0)

    def test_delete_ajax(self):
        url = reverse("main:delete_education", args=[self.education.id])

        self.login(self.editor)
        self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 403)

        self.login(self.owner)
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Education.objects.exists())


class ProjectAjaxTest(AjaxTestBase):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(
            title="Portfolio Website",
            description="My personal portfolio.",
            tech_stack="Django",
        )
        self.valid_data = {
            "title": "New Project",
            "description": "Something new.",
            "tech_stack": "Python",
            "project_url": "",
            "project_image_url": "",
        }

    def test_project_data_in_json(self):
        fields = self.client.get(reverse("main:get_projects_json")).json()[0]["fields"]

        self.assertEqual(fields["title"], "Portfolio Website")
        self.assertEqual(fields["star_count"], 0)
        self.assertFalse(fields["is_starred"])

    def test_create_permissions(self):
        self.login(self.editor)
        self.assertEqual(self.client.post(reverse("main:create_project_ajax"), self.valid_data).status_code, 403)

        self.login(self.owner)
        self.assertEqual(self.client.post(reverse("main:create_project_ajax"), self.valid_data).status_code, 201)

    def test_create_rejects_javascript_url(self):
        self.login(self.owner)
        response = self.client.post(
            reverse("main:create_project_ajax"),
            {**self.valid_data, "project_url": "javascript:alert(1)"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("project_url", response.json()["errors"])

    def test_edit_permissions(self):
        url = reverse("main:edit_project_ajax", args=[self.project.id])

        self.login(self.visitor)
        self.assertEqual(self.client.post(url, self.valid_data).status_code, 403)

        self.login(self.editor)
        self.assertEqual(self.client.post(url, self.valid_data).status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "New Project")

    def test_delete_ajax(self):
        self.login(self.owner)
        response = self.client.post(
            reverse("main:delete_project", args=[self.project.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.exists())
