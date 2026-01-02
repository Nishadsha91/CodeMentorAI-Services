import sys
import os
import time
import json
import pika
import django


sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "profile_service.settings")
django.setup()

from profiles.models import Profile, XPLog, ActivityLog, LearningHistory  # noqa: E402


# EVENT HANDLERS
def handle_problem_attempted(data):
    """User attempted a problem — record activity + learning history."""
    print("Handling problem.attempted:", data)

    user_id = data["user_id"]
    profile = Profile.objects.filter(user_id=user_id).first()

    if not profile:
        print("Profile not found for user:", user_id)
        return

    ActivityLog.objects.create(
        profile=profile,
        action_type="problem_attempted"
    )

    LearningHistory.objects.create(
        profile=profile,
        item_type="problem",
        item_title=data["problem_title"],
        status="attempted",
    )

    print(f"Updated activity for user {user_id} (attempted)")


def handle_problem_solved(data):
    """User solved a problem — add XP + logs + learning history."""
    print("Handling problem.solved:", data)

    user_id = data["user_id"]
    profile = Profile.objects.filter(user_id=user_id).first()

    if not profile:
        print("Profile not found for user:", user_id)
        return

    XP_REWARD = {"easy": 10, "medium": 20, "hard": 40}
    reward = XP_REWARD.get(data.get("difficulty"), 10)

    profile.xp += reward
    profile.save()

    XPLog.objects.create(
        profile=profile,
        amount=reward,
        reason=f"Solved problem: {data['problem_title']}"
    )

    ActivityLog.objects.create(
        profile=profile,
        action_type="problem_solved"
    )

    LearningHistory.objects.create(
        profile=profile,
        item_type="problem",
        item_title=data["problem_title"],
        status="solved",
    )

    print(f"User {user_id} solved {data['problem_title']} → +{reward} XP!")


# RABBITMQ CALLBACK
def callback(ch, method, properties, body):
    """Receives messages from RabbitMQ."""
    data = json.loads(body)
    event = data.get("event")

    print("EVENT RECEIVED:", event, data)

    if event == "user.created":
        Profile.objects.create(
            user_id=data["user_id"],
            full_name=data.get("full_name", ""),
            role=data.get("role", ""),
            bio="",
            country="",
            skills=[],
            xp=0,
            level=1,
            streak_days=0,
        )
        print("PROFILE CREATED for", data["user_id"])

    elif event == "problem.attempted":
        handle_problem_attempted(data)

    elif event == "problem.solved":
        handle_problem_solved(data)


# RABBITMQ CONNECTION
def connect_to_rabbitmq():
    while True:
        try:
            print("Connecting to RabbitMQ...")
            conn = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
            print("Connected to RabbitMQ!")
            return conn
        except Exception as e:
            print("RabbitMQ not ready, retrying...", str(e))
            time.sleep(3)


def start_consumer():
    while True:
        try:
            conn = connect_to_rabbitmq()
            channel = conn.channel()
            channel.queue_declare(queue="user_created")
            channel.queue_declare(queue="problem_attempted")
            channel.queue_declare(queue="problem_solved")

            print("Profile-Service listening for events...")

            channel.basic_consume(
                queue="user_created", on_message_callback=callback, auto_ack=True
            )
            channel.basic_consume(
                queue="problem_attempted", on_message_callback=callback, auto_ack=True
            )
            channel.basic_consume(
                queue="problem_solved", on_message_callback=callback, auto_ack=True
            )

            channel.start_consuming()

        except Exception as e:
            print("Consumer error:", e)
            time.sleep(3)


# ENTRY POINT
if __name__ == "__main__":
    start_consumer()
