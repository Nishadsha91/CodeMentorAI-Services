from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ForgotPasswordView,
    ResetPasswordView,
    GoogleLoginView,
    GithubLoginView
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/<uid>/<token>/", ResetPasswordView.as_view()),
    path("google/login/", GoogleLoginView.as_view()),
    path("github/login/", GithubLoginView.as_view()),
]
