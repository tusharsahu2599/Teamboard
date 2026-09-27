from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import KBEntry, QueryLog
from .permissions import IsAdminUser


def _access_token(user):
    return str(RefreshToken.for_user(user).access_token)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        company_name = request.data.get("company_name")
        email = request.data.get("email")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (username, password, company_name, email)
        ):
            return Response(
                {"error": "username, password, company_name, and email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = username.strip()
        company_name = company_name.strip()
        email = email.strip()

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
        )
        company = user.company
        company.company_name = company_name
        company.save(update_fields=["company_name"])

        return Response(
            {
                "username": user.username,
                "company_name": company.company_name,
                "api_key": company.api_key,
                "access": _access_token(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not isinstance(username, str) or not isinstance(password, str):
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        company = user.company
        return Response(
            {
                "access": _access_token(user),
                "company_name": company.company_name,
                "api_key": company.api_key,
            },
            status=status.HTTP_200_OK,
        )


class KBQueryView(APIView):
    def post(self, request):
        search = request.data.get("search")
        if not isinstance(search, str) or not search.strip():
            return Response(
                {"error": "search is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        search_term = search.strip()
        if len(search_term) > 255:
            return Response(
                {"error": "search must be at most 255 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        company = request.user.company
        with transaction.atomic():
            matches = KBEntry.objects.filter(
                Q(question__icontains=search_term) | Q(answer__icontains=search_term)
            ).order_by("id")
            count = matches.count()
            QueryLog.objects.create(
                company=company,
                search_term=search_term,
                results_count=count,
            )
            results = [
                {
                    "id": str(entry.id),
                    "question": entry.question,
                    "answer": entry.answer,
                    "category": entry.category,
                }
                for entry in matches
            ]

        return Response(
            {
                "search": search_term,
                "count": count,
                "results": results,
            },
            status=status.HTTP_200_OK,
        )


class UsageSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_queries = QueryLog.objects.aggregate(total=Count("id"))["total"]
        active_companies = QueryLog.objects.values("company").distinct().count()
        top_search_terms = list(
            QueryLog.objects.values("search_term")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        return Response(
            {
                "total_queries": total_queries,
                "active_companies": active_companies,
                "top_search_terms": top_search_terms,
            },
            status=status.HTTP_200_OK,
        )
