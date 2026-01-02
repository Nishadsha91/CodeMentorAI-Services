from django.urls import path
from .views import (
    ProfileCreateView,
    ProfileDetailView,
    ProfileUpdateView,
    AddXPView,
    XPLogListView,
    AchievementListView,
    UserAchievementListView,
    ActivityOverviewView,
    LearningHistoryView,
    UpdateStreakView,
)

urlpatterns = [
    path("create/", ProfileCreateView.as_view(), name="profile-create"),
    path("user/<int:user_id>/", ProfileDetailView.as_view(), name="profile-detail"),
    path("user/<int:user_id>/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path("user/<int:user_id>/xp/add/", AddXPView.as_view(), name="add-xp"),
    path("user/<int:user_id>/xp/logs/", XPLogListView.as_view(), name="xp-logs"),
    path("user/<int:user_id>/streak/update/", UpdateStreakView.as_view(), name="update-streak"),
    path("achievements/", AchievementListView.as_view(), name="achievement-list"),
    path("user/<int:user_id>/achievements/", UserAchievementListView.as_view(), name="user-achievements"),
    path("user/<int:user_id>/activity/", ActivityOverviewView.as_view(), name="activity-overview"),
    path("user/<int:user_id>/learning-history/", LearningHistoryView.as_view(), name="learning-history"),
]
