from django.contrib import admin
from django import forms
from .models import Problem, Attempt
import json

class ProblemAdminForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = "__all__"

    def clean_tags(self):
        tags = self.cleaned_data.get("tags")
        if isinstance(tags, str):
            try:
                return json.loads(tags)
            except Exception:
                raise forms.ValidationError("Tags must be a JSON list, e.g. [\"array\",\"dp\"]")
        return tags

    def clean_examples(self):
        ex = self.cleaned_data.get("examples")
        if isinstance(ex, str):
            try:
                return json.loads(ex)
            except Exception:
                raise forms.ValidationError("Examples must be valid JSON list")
        return ex

    def clean_starter_code(self):
        sc = self.cleaned_data.get("starter_code")
        if isinstance(sc, str):
            try:
                return json.loads(sc)
            except Exception:
                raise forms.ValidationError("starter_code must be a JSON object, e.g. {\"python\":\"...\"}")
        return sc

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    form = ProblemAdminForm
    list_display = ("title", "slug", "difficulty", "category", "acceptance", "created_at")
    search_fields = ("title", "description", "tags")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "slug", "difficulty", "category", "acceptance")}),
        ("Content", {"fields": ("description", "examples", "starter_code", "constraints", "tags")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("user_id", "problem", "language", "created_at")
    search_fields = ("user_id", "problem__title")
