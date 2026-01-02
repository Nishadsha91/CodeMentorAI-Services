import uuid
from django.db import models

def generate_session_code():
    """Generate a unique 12-character session code"""
    return uuid.uuid4().hex[:12].upper()

class PairSession(models.Model):
    SESSION_STATUS = (
        ("waiting", "Waiting"),
        ("active", "Active"),
        ("ended", "Ended"),
    )
    SESSION_MODE = (
        ("collaborative", "Both can edit"),
        ("observer", "Guest view only"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_code = models.CharField(
        max_length=12, 
        unique=True,
        default=generate_session_code  # Auto-generate on creation
    )
    host_id = models.IntegerField()     # user_id from auth-service
    guest_id = models.IntegerField(null=True, blank=True)
    problem_id = models.IntegerField()  # ID of the problem being solved

    language = models.CharField(
        max_length=20,
        choices=[
            ("javascript", "JavaScript"),
            ("python", "Python"),
            ("java", "Java"),
            ("cpp", "C++"),
        ]
    )

    mode = models.CharField(
        max_length=20,
        choices=SESSION_MODE,
        default="collaborative"
    )

    status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS,
        default="waiting"
    )

    is_public = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.id} ({self.language})"


class PairSessionParticipant(models.Model):
    ROLE_CHOICES = (
        ("host", "Host"),
        ("guest", "Guest"),
    )

    session = models.ForeignKey(
        PairSession,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    user_id = models.IntegerField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("session", "user_id")