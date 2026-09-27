from django.contrib.auth.models import User
from django.db import models


class Company(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CLIENT = "client", "Client"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="company",
    )
    company_name = models.CharField(max_length=255)
    api_key = models.CharField(max_length=64, unique=True, blank=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name


class KBEntry(models.Model):
    class Category(models.TextChoices):
        API = "api", "API"
        DATABASE = "database", "Database"
        CLOUD = "cloud", "Cloud"
        FRAMEWORK = "framework", "Framework"
        GENERAL = "general", "General"

    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question[:80]


class QueryLog(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="query_logs",
    )
    search_term = models.CharField(max_length=255)
    results_count = models.IntegerField()
    queried_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_id}: {self.search_term}"
