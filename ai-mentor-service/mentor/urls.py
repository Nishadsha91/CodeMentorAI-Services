from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeedbackViewSet, CodeFeedbackViewSet

router = DefaultRouter()
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'cached', CodeFeedbackViewSet, basename='cached-feedback')

urlpatterns = [
    path('', include(router.urls)),
]