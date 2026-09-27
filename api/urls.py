from django.urls import path

from .views import KBQueryView, LoginView, RegisterView, UsageSummaryView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("kb/query/", KBQueryView.as_view(), name="kb-query"),
    path("admin/usage-summary/", UsageSummaryView.as_view(), name="usage-summary"),
]
