from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Company, KBEntry, QueryLog


class TeamBoardAPITests(APITestCase):
    def setUp(self):
        KBEntry.objects.create(
            question="What is select_related in Django ORM?",
            answer="select_related performs a SQL JOIN and fetches related rows.",
            category=KBEntry.Category.DATABASE,
        )
        KBEntry.objects.create(
            question="How does select_related differ from prefetch_related?",
            answer="prefetch_related uses a separate query.",
            category=KBEntry.Category.DATABASE,
        )

    def _register(self, username="acmecorp", company_name="Acme Corp", **extra):
        payload = {
            "username": username,
            "password": "securepass123",
            "company_name": company_name,
            "email": f"{username}@example.com",
        }
        payload.update(extra)
        return self.client.post("/api/auth/register/", payload, format="json")

    def test_register_returns_token_and_api_key(self):
        response = self._register(role="admin")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.data
        self.assertEqual(body["username"], "acmecorp")
        self.assertEqual(body["company_name"], "Acme Corp")
        self.assertTrue(body["api_key"])
        self.assertTrue(body["access"])

        company = Company.objects.get(user__username="acmecorp")
        self.assertEqual(company.api_key, body["api_key"])
        self.assertEqual(company.role, Company.Role.CLIENT)
        self.assertEqual(company.company_name, "Acme Corp")

    def test_register_duplicate_username(self):
        self._register()
        response = self._register()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Username already exists")
        self.assertEqual(User.objects.filter(username="acmecorp").count(), 1)

    def test_login_returns_credentials(self):
        registered = self._register()
        response = self.client.post(
            "/api/auth/login/",
            {"username": "acmecorp", "password": "securepass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company_name"], "Acme Corp")
        self.assertEqual(response.data["api_key"], registered.data["api_key"])
        self.assertTrue(response.data["access"])

    def test_login_invalid_credentials(self):
        self._register()
        response = self.client.post(
            "/api/auth/login/",
            {"username": "acmecorp", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_query_requires_token(self):
        response = self.client.post(
            "/api/kb/query/",
            {"search": "select_related"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_query_matches_question_or_answer_case_insensitively(self):
        self._register()
        self.client.post(
            "/api/auth/login/",
            {"username": "acmecorp", "password": "securepass123"},
            format="json",
        )
        login = self.client.post(
            "/api/auth/login/",
            {"username": "acmecorp", "password": "securepass123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = self.client.post(
            "/api/kb/query/",
            {"search": "SELECT_RELATED"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertTrue(all(isinstance(row["id"], str) for row in response.data["results"]))
        self.assertEqual(QueryLog.objects.count(), 1)
        self.assertEqual(QueryLog.objects.get().results_count, 2)
        self.assertEqual(QueryLog.objects.get().search_term, "SELECT_RELATED")

    def test_query_blank_search(self):
        registered = self._register()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {registered.data['access']}")
        response = self.client.post("/api/kb/query/", {"search": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(QueryLog.objects.count(), 0)

    def test_query_no_matches_still_logs(self):
        registered = self._register()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {registered.data['access']}")
        response = self.client.post(
            "/api/kb/query/",
            {"search": "no-such-topic"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])
        self.assertEqual(QueryLog.objects.get().results_count, 0)

    def test_usage_summary_forbidden_for_client(self):
        registered = self._register()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {registered.data['access']}")
        response = self.client.get("/api/admin/usage-summary/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_usage_summary_requires_token(self):
        response = self.client.get("/api/admin/usage-summary/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usage_summary_for_admin(self):
        first = self._register(username="acmecorp", company_name="Acme Corp")
        second = self._register(username="otherco", company_name="Other Co")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {first.data['access']}")
        self.client.post("/api/kb/query/", {"search": "select_related"}, format="json")
        self.client.post("/api/kb/query/", {"search": "select_related"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {second.data['access']}")
        self.client.post("/api/kb/query/", {"search": "prefetch"}, format="json")

        company = Company.objects.get(user__username="acmecorp")
        company.role = Company.Role.ADMIN
        company.save(update_fields=["role"])

        login = self.client.post(
            "/api/auth/login/",
            {"username": "acmecorp", "password": "securepass123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get("/api/admin/usage-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_queries"], 3)
        self.assertEqual(response.data["active_companies"], 2)
        self.assertEqual(response.data["top_search_terms"][0]["search_term"], "select_related")
        self.assertEqual(response.data["top_search_terms"][0]["count"], 2)
