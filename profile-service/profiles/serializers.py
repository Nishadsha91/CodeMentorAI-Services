from rest_framework import serializers
from .models import ( Profile,XPLog,Achievement,UserAchievement,ActivityLog,LearningHistory,)

# PROFILE SERIALIZERS
class ProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["user_id", "full_name", "role"]

    def create(self, validated_data):
        return Profile.objects.create(

            user_id=validated_data["user_id"],
            full_name=validated_data.get("full_name", ""),
            role=validated_data.get("role", ""),
            bio="",
            country="",
            skills=[],
            github_url="",
            linkedin_url="",
            profile_image=None,
            xp=0,
            level=1,
            streak_days=0,
        )



class ProfileSerializer(serializers.ModelSerializer):
    """Main serializer returned to frontend."""

    skills = serializers.JSONField(default=list)

    class Meta:
        model = Profile
        fields = [
            "user_id",
            "full_name",
            "role",
            "bio",
            "country",
            "skills",
            "github_url",
            "linkedin_url",
            "profile_image",
            "xp",
            "level",
            "streak_days",
            "created_at",
            "updated_at",
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Patch serializer for updating profile.
    Accepts JSON, FormData and image uploads.
    """

    skills = serializers.JSONField(required=False)
    profile_image = serializers.ImageField(required=False)
    

    class Meta:
        model = Profile
        fields = [
            "full_name",
            "role",
            "bio",
            "country",
            "skills",
            "github_url",
            "linkedin_url",
            "profile_image",
        ]


# XP LOGS
class XPLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = XPLog
        fields = ["id", "amount", "reason", "created_at"]


# ACHIEVEMENTS
class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ["id", "name", "description", "icon"]


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ["achievement", "earned_at"]


# ACTIVITY LOG
class ActivityLogSerializer(serializers.ModelSerializer):
    """
    Includes action type + timestamp for frontend graph.
    """

    class Meta:
        model = ActivityLog
        fields = ["action_type", "created_at"]


# LEARNING HISTORY
class LearningHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningHistory
        fields = ["item_type", "item_title", "status", "timestamp"]
