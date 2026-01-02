from rest_framework import serializers
from .models import CodeFeedback, FeedbackRequest

class CodeFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeFeedback
        fields = [
            'id',
            'code',
            'language',
            'problem_id',
            'user_id',
            'feedback',
            'scores',
            'interview_ready_score',
            'tokens_used',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'tokens_used']


class FeedbackRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackRequest
        fields = [
            'id', 'code', 'problem_description', 'language', 
            'problem_id', 'user_id', 'status', 'feedback', 
            'error_message', 'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'feedback', 'error_message', 
            'created_at', 'completed_at', 'celery_task_id'
        ]


class AnalyzeCodeRequestSerializer(serializers.Serializer):
    code = serializers.CharField()
    problem_description = serializers.CharField()
    language = serializers.ChoiceField(
        choices=['python', 'javascript', 'java', 'cpp', 'csharp']
    )
    explanation = serializers.CharField(required=False, allow_blank=True)
    time_taken_seconds = serializers.IntegerField(required=False)

    problem_id = serializers.IntegerField(required=False, allow_null=True)
    user_id = serializers.IntegerField(required=False, allow_null=True)
