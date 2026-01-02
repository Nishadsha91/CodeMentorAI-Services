from django.db import models
from datetime import date, timedelta



# PROFILE MODEL
class Profile(models.Model):
    user_id = models.IntegerField(unique=True, db_index=True)   
    full_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=50)   
    bio = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    skills = models.JSONField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    streak_days = models.IntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Profile of User {self.user_id}"
    

    def get_week_streak(self):
        today = date.today()

        # Prepare Mon–Sun
        week_days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

        completed_days = set()

        if self.streak_days > 0 and self.last_active_date:
            days_to_mark = min(self.streak_days, 7)
            for i in range(days_to_mark):
                day = (today - timedelta(days=i)).weekday()  
                completed_days.add(day)

        week_data = []
        for idx, label in enumerate(week_days):
            week_data.append({
                "day": label,
                "completed": idx in completed_days
            })

        return week_data

    # XP SYSTEM
    def add_xp(self, amount, reason=""):
        """Add XP and auto update level + log"""
        self.xp += amount
        self.level = max(1, (self.xp // 1000) + 1)
        self.save()

        XPLog.objects.create(
            user_id=self.user_id,
            amount=amount,
            reason=reason,
        )

    # STREAK SYSTEM
    def update_streak(self):
        today = date.today()

        # First login today → give XP
        is_new_day = (self.last_active_date != today)

        if self.last_active_date == today - timedelta(days=1):
            self.streak_days += 1
        elif self.last_active_date == today:
            pass
        else:
            self.streak_days = 1

        self.last_active_date = today
        self.save()

        # XP reward for daily login
        if is_new_day:
            self.add_xp(2, "Daily Login Reward")

        # Log activity
        ActivityLog.objects.create(
            user_id=self.user_id,
            action_type="login"
        )


# XP LOGS
class XPLog(models.Model):
    user_id = models.IntegerField(db_index=True)
    amount = models.IntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"XP {self.amount} for user {self.user_id}"



# ACHIEVEMENTS
class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=200)

    def __str__(self):
        return self.name

# USER ACHIEVEMENTS
class UserAchievement(models.Model):
    user_id = models.IntegerField(db_index=True)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-earned_at"]

    def __str__(self):
        return f"{self.user_id} - {self.achievement.name}"

# ACTIVITY LOG (monthly chart data)
class ActivityLog(models.Model):
    ACTION_TYPES = [
        ("login", "Login"),
        ("solve_problem", "Solve Problem"),
        ("run_code", "Run Code"),
        ("submit_answer", "Submit Answer"),
    ]

    user_id = models.IntegerField(db_index=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} - {self.action_type}"


# LEARNING HISTORY
class LearningHistory(models.Model):
    ITEM_TYPES = [
        ("problem", "Coding Problem"),
        ("lesson", "Lesson"),
        ("interview", "Interview Simulation"),
    ]

    user_id = models.IntegerField(db_index=True)
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES)
    item_title = models.CharField(max_length=200)
    status = models.CharField(max_length=50, default="completed")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user_id} - {self.item_title}"
