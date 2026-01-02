from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "full_name", "role", "country", "created_at")
    search_fields = ("full_name", "user_id", "country", "github_url", "linkedin_url")
