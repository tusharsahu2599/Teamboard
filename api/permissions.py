from rest_framework.permissions import BasePermission

from .models import Company


class IsAdminUser(BasePermission):
    message = "Admin access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            company = user.company
        except Company.DoesNotExist:
            return False
        return company.role == Company.Role.ADMIN
