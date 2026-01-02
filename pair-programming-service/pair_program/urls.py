from django.urls import path
from .views import (
    CreateSessionAPIView,
    JoinSessionAPIView,
    PublicSessionsAPIView,
    EndSessionAPIView,
    GetSessionAPIView
)

urlpatterns = [
    path("sessions/create/", CreateSessionAPIView.as_view()),
    path("sessions/join/", JoinSessionAPIView.as_view()),
    path("sessions/public/", PublicSessionsAPIView.as_view()),
    path("sessions/<uuid:session_id>/end/", EndSessionAPIView.as_view()),
    path('sessions/<uuid:session_id>/', GetSessionAPIView.as_view()),
]
