from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models.functions import ExtractMonth
from django.db.models import Count
from .models import (Profile, XPLog, Achievement, UserAchievement,ActivityLog, LearningHistory)
from .serializers import ( ProfileSerializer, ProfileUpdateSerializer, ProfileCreateSerializer,XPLogSerializer, AchievementSerializer, UserAchievementSerializer,LearningHistorySerializer)

# PROFILE CREATE
class ProfileCreateView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        serializer = ProfileCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile created"}, status=201)

        print("PROFILE CREATE ERROR:", serializer.errors)
        return Response(serializer.errors, status=400)



# GET PROFILE
class ProfileDetailView(APIView):
    parser_classes = [JSONParser]

    def get(self, request, user_id):
        profile = get_object_or_404(Profile, user_id=user_id)
        profile.update_streak()
        profile_data = ProfileSerializer(profile).data
        all_achievements = AchievementSerializer(Achievement.objects.all(), many=True).data
        user_badges = UserAchievementSerializer(
            UserAchievement.objects.filter(user_id=user_id),
            many=True
        ).data
        activity_logs = (
            ActivityLog.objects
            .filter(user_id=user_id)
            .annotate(month=ExtractMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        activity = [
            {"month": log["month"], "count": log["count"]}
            for log in activity_logs
        ]
        learning_history = LearningHistorySerializer(
            LearningHistory.objects.filter(user_id=user_id).order_by("-timestamp"),
            many=True
        ).data

        return Response({
            "profile": profile_data,
            "achievements": all_achievements,
            "user_achievements": user_badges,
            "activity": activity,
            "learning_history": learning_history,
            "weekly_streak": profile.get_week_streak(),

        })



# UPDATE PROFILE 
class ProfileUpdateView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    def patch(self, request, user_id):
        profile = get_object_or_404(Profile, user_id=user_id)

        serializer = ProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(ProfileSerializer(profile).data, status=200)

        print("PROFILE UPDATE ERROR:", serializer.errors)
        return Response(serializer.errors, status=400)


# XP SYSTEM
class AddXPView(APIView):
    def post(self, request, user_id):
        profile = get_object_or_404(Profile, user_id=user_id)

        amount = int(request.data.get("amount", 0))
        reason = request.data.get("reason", "")

        profile.add_xp(amount, reason)

        return Response({"message": "XP added"}, status=200)


class XPLogListView(APIView):
    def get(self, request, user_id):
        logs = XPLog.objects.filter(user_id=user_id).order_by("-created_at")
        return Response(XPLogSerializer(logs, many=True).data)


# STREAK
class UpdateStreakView(APIView):
    def post(self, request, user_id):
        profile = get_object_or_404(Profile, user_id=user_id)
        profile.update_streak()
        return Response({"message": "Streak updated"}, status=200)


# ACHIEVEMENTS
class AchievementListView(APIView):
    def get(self, request):
        items = Achievement.objects.all()
        return Response(AchievementSerializer(items, many=True).data)


class UserAchievementListView(APIView):
    def get(self, request, user_id):
        items = UserAchievement.objects.filter(user_id=user_id)
        return Response(UserAchievementSerializer(items, many=True).data)


# ACTIVITY LOG — MONTHLY CHART
class ActivityOverviewView(APIView):
    def get(self, request, user_id):

        logs = (
            ActivityLog.objects
            .filter(user_id=user_id)
            .annotate(month=ExtractMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        monthly_data = [
            {"month": log["month"], "count": log["count"]}
            for log in logs
        ]

        return Response(monthly_data)


# LEARNING HISTORY
class LearningHistoryView(APIView):
    def get(self, request, user_id):
        history = (
            LearningHistory.objects
            .filter(user_id=user_id)
            .order_by("-timestamp")
        )
        return Response(LearningHistorySerializer(history, many=True).data)
