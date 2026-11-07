import uuid

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from main.models import Education, Project


class ProjectAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.visitor = User.objects.create_user(username="visitor", password="test-password")
        self.project = Project.objects.create(
            title="Portfolio", description="My website", tech_stack="Django",
        )
        self.list_url = reverse("api:project-list")
        self.detail_url = reverse("api:project-detail", args=[self.project.id])
        self.star_url = reverse("api:project-star", args=[self.project.id])
        self.payload = {
            "title": "New project", "description": "A useful app", "tech_stack": "Python",
            "project_url": "https://example.com/", "project_image_url": "",
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.project.id))
        self.assertFalse(response.data[0]["is_starred"])
        self.assertNotIn("fields", response.data[0])
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    def test_search_and_empty_results(self):
        response = self.client.get(self.list_url, {"title": "PORT"})
        self.assertEqual(len(response.data), 1)
        response = self.client.get(self.list_url, {"title": "not-found"})
        self.assertEqual(response.data, [])

    def test_missing_project(self):
        url = reverse("api:project-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
            self.assertEqual(self.client.patch(self.detail_url, {"title": "Changed"}, format="json").status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Portfolio")

    def test_owner_can_create(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Project.objects.filter(pk=response.data["id"]).exists())

    def test_validation(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in [
            ({"title": "   "}, "title"),
            ({"title": '<img src="x" onerror="alert(1)">'}, "title"),
            ({"project_url": "javascript:alert(1)"}, "project_url"),
        ]:
            response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assertEqual(Project.objects.count(), 1)

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.description, "My website")
        response = self.client.put(self.detail_url, {"title": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload, "star_count": 99, "is_starred": True,
            "starred_by_names": "forged", "starred_by": [self.visitor.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])

    def test_staff_and_editor_cannot_manage_tutorial_projects(self):
        self.visitor.is_staff = True
        self.visitor.save()
        self.visitor.groups.add(Group.objects.create(name="Editor"))
        self.client.force_authenticate(user=self.visitor)
        response = self.client.patch(self.detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Project.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="owner", password="test-password")
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class EducationAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.editor = User.objects.create_user(username="editor", password="test-password")
        self.editor.groups.add(Group.objects.create(name="Editor"))
        self.regular = User.objects.create_user(username="regular", password="test-password")
        self.education = Education.objects.create(
            institution="Universitas Indonesia", faculty_or_major="Ilmu Komputer",
            degree="S1", started_at="2025-08-01", description="Computer Science",
        )
        self.list_url = reverse("api:education-list")
        self.detail_url = reverse("api:education-detail", args=[self.education.id])
        self.star_url = reverse("api:education-star", args=[self.education.id])
        self.payload = {
            "institution": "SMA Negeri 8", "faculty_or_major": "IPA", "degree": "SMA",
            "started_at": "2022-07-01", "ended_at": "2025-06-01", "description": "",
        }

    def assert_education_unchanged(self):
        self.assertEqual(Education.objects.count(), 1)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Universitas Indonesia")
        self.assertEqual(self.education.description, "Computer Science")
        self.assertIsNone(self.education.ended_at)

    def test_visitor_can_read_list_detail_and_search(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.education.id))
        self.assertTrue(response.data[0]["is_ongoing"])
        self.assertNotIn("fields", response.data[0])
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)
        response = self.client.get(self.list_url, {"institution": "UNIVERSITAS"})
        self.assertEqual(len(response.data), 1)
        response = self.client.get(self.list_url, {"institution": "not-found"})
        self.assertEqual(response.data, [])
        self.assertEqual(self.client.options(self.list_url).status_code, status.HTTP_200_OK)
        self.assert_education_unchanged()

    def test_missing_education_returns_404(self):
        missing_url = reverse("api:education-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(missing_url).status_code, status.HTTP_404_NOT_FOUND)
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.patch(missing_url, {"degree": "S2"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(missing_url).status_code, 404)
        self.assert_education_unchanged()

    def test_visitor_and_regular_user_cannot_write(self):
        for user in (None, self.regular):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
            self.assertEqual(self.client.put(self.detail_url, self.payload, format="json").status_code, 403)
            self.assertEqual(self.client.patch(self.detail_url, {"description": "Changed"}, format="json").status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
            self.assert_education_unchanged()

    def test_editor_can_patch_and_put(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"description": "Edited by editor"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.education.refresh_from_db()
        self.assertEqual(self.education.description, "Edited by editor")
        self.assertEqual(self.education.institution, "Universitas Indonesia")

        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "SMA Negeri 8")
        self.assertFalse(self.education.is_ongoing)

    def test_editor_cannot_create_or_delete(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)
        self.assertEqual(self.client.delete(self.detail_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assert_education_unchanged()

    def test_owner_can_create_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Education.objects.filter(pk=response.data["id"]).exists())

        response = self.client.patch(self.detail_url, {"degree": "S2"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.education.refresh_from_db()
        self.assertEqual(self.education.degree, "S2")

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Education.objects.filter(pk=self.education.id).exists())

    def test_tag_only_or_whitespace_input_is_rejected(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in [
            ({"institution": "   "}, "institution"),
            ({"institution": "<b></b>"}, "institution"),
            ({"faculty_or_major": "<i> </i>"}, "faculty_or_major"),
            ({"degree": '<img src="x" onerror="alert(1)">'}, "degree"),
        ]:
            response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assert_education_unchanged()

    def test_html_tags_are_stripped(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload,
            "institution": "<b>SMA</b> Negeri 8",
            "description": "  <script>alert(1)</script>Science class  ",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Education.objects.get(pk=response.data["id"])
        self.assertEqual(created.institution, "SMA Negeri 8")
        self.assertEqual(created.description, "alert(1)Science class")

    def test_invalid_dates_are_rejected(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in [
            ({"started_at": "not-a-date"}, "started_at"),
            ({"ended_at": ""}, "ended_at"),
            ({"ended_at": "2020-01-01"}, "ended_at"),
        ]:
            response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)

        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"ended_at": "2024-01-01"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ended_at", response.data)
        self.assert_education_unchanged()

    def test_guest_cannot_star(self):
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.education.starred_by.count(), 0)

    def test_star_toggles_for_the_logged_in_user(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(self.star_url, {"user": self.owner.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        self.assertEqual(list(self.education.starred_by.all()), [self.regular])

        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(self.education.starred_by.exists())

        self.assertEqual(self.client.get(self.star_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_computed_fields_are_read_only(self):
        forged_id = uuid.uuid4()
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload, "ended_at": None, "id": str(forged_id),
            "star_count": 99, "is_starred": True, "is_ongoing": False,
            "starred_by_names": "forged", "starred_by": [self.regular.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data["id"], str(forged_id))
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertTrue(response.data["is_ongoing"])
        self.assertEqual(response.data["starred_by_names"], "")
        self.assertFalse(Education.objects.get(pk=response.data["id"]).starred_by.exists())

    def test_responses_do_not_expose_account_data(self):
        self.education.starred_by.add(self.owner, self.regular)
        self.client.force_authenticate(user=self.regular)
        responses = [
            self.client.get(self.list_url),
            self.client.get(self.detail_url),
            self.client.post(self.star_url),
        ]
        for response in responses:
            body = response.content.decode()
            self.assertNotIn("email", body)
            self.assertNotIn("owner@example.com", body)
            self.assertNotIn("password", body)
            self.assertNotIn("pbkdf2", body)
        self.assertEqual(responses[1].data["starred_by_names"], "owner, regular")

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("CSRF", response.data["detail"])
        self.assertEqual(Education.objects.count(), 1)

        client.get(reverse("main:show_education"))
        token = client.cookies["csrftoken"].value
        response = client.post(self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Education.objects.count(), 2)

    def test_education_page_gives_regular_users_a_csrf_token_for_starring(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="regular", password="test-password"))
        self.assertEqual(client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(self.education.starred_by.exists())

        client.get(reverse("main:show_education"))
        token = client.cookies["csrftoken"].value
        response = client.post(self.star_url, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.education.starred_by.filter(pk=self.regular.pk).exists())
