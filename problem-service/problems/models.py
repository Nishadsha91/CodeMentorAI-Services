from django.db import models
from django.utils import timezone


class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=200)

    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="easy")
    category = models.CharField(max_length=100, blank=True)
    acceptance = models.FloatField(default=0.0)

    description = models.TextField(blank=True)
    input_format = models.TextField(blank=True)
    output_format = models.TextField(blank=True)

    examples = models.JSONField(default=list, blank=True)
    starter_code = models.JSONField(default=dict, blank=True)
    constraints = models.JSONField(default=list, blank=True)
    solution_outline = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# SUBMISSION
class Attempt(models.Model):
    """
    Attempt = user submission record
    Execution result + AI review results are stored in separate linked models.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user_id = models.IntegerField() 
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="attempts")
    code = models.TextField(blank=True)
    language = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Attempt(User:{self.user_id} Problem:{self.problem.slug} Status:{self.status})"


# EXECUTION RESULT
class ExecutionResult(models.Model):
    """
    Stores execution output returned from Execution Service.
    """
    attempt = models.OneToOneField(Attempt, on_delete=models.CASCADE, related_name="execution_result")
    stdout = models.TextField(blank=True, null=True)
    stderr = models.TextField(blank=True, null=True)
    results = models.JSONField(default=dict)  
    passed = models.BooleanField(default=False)
    runtime = models.FloatField(default=0.0) 
    memory = models.IntegerField(default=0)   

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ExecutionResult(Attempt:{self.attempt.id}, Passed:{self.passed})"


# AI REVIEW RESULT
class AIReview(models.Model):
    """
    AI reasoning output for each attempt.
    """
    attempt = models.OneToOneField(Attempt, on_delete=models.CASCADE, related_name="ai_review")
    scores = models.JSONField(default=dict) 
    summary = models.TextField(blank=True)
    full_feedback = models.TextField(blank=True)
    suggested_code = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"AIReview(Attempt:{self.attempt.id})"


# TEST CASES
class TestCase(models.Model):

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="testcases")
    input = models.TextField()
    output = models.TextField()
    hidden = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"TestCase (Problem: {self.problem.title}, Hidden: {self.hidden})"
