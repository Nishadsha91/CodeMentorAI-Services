from django.db import models
import hashlib


class CodeFeedback(models.Model):
    """
    Cached AI feedback for submitted code.
    Used to avoid duplicate OpenAI calls.
    """

    code_hash = models.CharField(max_length=64, unique=True, db_index=True)
    code = models.TextField()
    problem_description = models.TextField()
    language = models.CharField(max_length=20)
    problem_id = models.IntegerField(null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True)
    feedback = models.JSONField()
    scores = models.JSONField()
    interview_ready_score = models.FloatField(null=True, blank=True)
    tokens_used = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cached Feedback | Problem {self.problem_id} | {self.language}"

    @staticmethod
    def generate_hash(code: str, problem_id: int | None) -> str:
        combined = f"{code}_{problem_id}"
        return hashlib.sha256(combined.encode()).hexdigest()


class FeedbackRequest(models.Model):
    """
    Tracks async AI mentor review requests
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    code = models.TextField()
    problem_description = models.TextField()
    language = models.CharField(max_length=20)
    explanation = models.TextField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(null=True, blank=True)

    problem_id = models.IntegerField(null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True)

    status = models.CharField( max_length=20, choices=STATUS_CHOICES, default="pending")
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)

    # AI OUTPUT
    feedback = models.JSONField(null=True, blank=True)
    scores = models.JSONField(null=True, blank=True)
    interview_ready_score = models.FloatField(null=True, blank=True)

    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Request {self.id} | {self.status}"
