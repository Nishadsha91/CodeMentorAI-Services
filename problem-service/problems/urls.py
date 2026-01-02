from django.urls import path
from .views import AttemptDetailView, ProblemListView, ProblemDetailView, CreateAttemptView, SubmitAttemptView, RunCodeView

urlpatterns = [
    path("problems/", ProblemListView.as_view(), name="problem-list"),
    path("problems/<slug:slug>/", ProblemDetailView.as_view(), name="problem-detail"),

    path("problems/<slug:slug>/attempt/", CreateAttemptView.as_view(), name="attempt-create"),
    path("problems/<slug:slug>/submit/", SubmitAttemptView.as_view(), name="attempt-submit"),
    path("problems/<slug:slug>/run/", RunCodeView.as_view(), name="code-run"),


    path("attempts/<int:attempt_id>/", AttemptDetailView.as_view(), name="attempt-detail"),
]
