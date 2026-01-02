from django.urls import path
from .views import ResumeEnhanceView

urlpatterns = [
    path('enhance/', ResumeEnhanceView.as_view(), name='resume-enhance'),
]
