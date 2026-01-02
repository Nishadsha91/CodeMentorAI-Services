from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CodeFeedback, FeedbackRequest
from .serializers import (
    CodeFeedbackSerializer, 
    FeedbackRequestSerializer,
    AnalyzeCodeRequestSerializer
)
from .tasks import analyze_code_async
import logging

logger = logging.getLogger(__name__)

class FeedbackViewSet(viewsets.ModelViewSet):
    """API endpoints for code feedback"""
    
    queryset = FeedbackRequest.objects.all()
    serializer_class = FeedbackRequestSerializer
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """
        Analyze submitted code and get AI feedback
        """
        serializer = AnalyzeCodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        problem_desc = serializer.validated_data['problem_description']
        language = serializer.validated_data['language']
        problem_id = serializer.validated_data.get('problem_id')
        user_id = serializer.validated_data.get('user_id')
        
        logger.info(f" [API] New feedback request for problem {problem_id} - {language}")
        
        #feedback request
        feedback_request = FeedbackRequest.objects.create(
            code=code,
            problem_description=problem_desc,
            language=language,
            explanation=serializer.validated_data.get("explanation"),
            time_taken_seconds=serializer.validated_data.get("time_taken_seconds"),
            problem_id=problem_id,
            user_id=user_id,
        )

        
        #async task
        task = analyze_code_async.delay(feedback_request.id)
        feedback_request.celery_task_id = task.id
        feedback_request.save()
        
        logger.info(f"[API] Task {task.id} started for request {feedback_request.id}")
        
        return Response(
            {
                'request_id': feedback_request.id,
                'task_id': task.id,
                'status': 'processing',
                'message': 'Your code is being analyzed. Check back in a few seconds.'
            },
            status=status.HTTP_202_ACCEPTED
        )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Get status of a feedback request
        
        GET /api/feedback/{id}/status/
        """
        feedback_request = self.get_object()
        
        return Response({
            'request_id': feedback_request.id,
            'status': feedback_request.status,
            'feedback': feedback_request.feedback,
            'error': feedback_request.error_message,
            'created_at': feedback_request.created_at,
            'completed_at': feedback_request.completed_at
        })
    
    @action(detail=False, methods=['get'])
    def user_feedback(self, request):
        """
        Get all feedback for a user
        
        GET /api/feedback/user_feedback/?user_id=123
        """
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedbacks = FeedbackRequest.objects.filter(
            user_id=user_id,
            status='completed'
        ).order_by('-created_at')[:10] 
        
        serializer = self.get_serializer(feedbacks, many=True)
        return Response(serializer.data)


class CodeFeedbackViewSet(viewsets.ReadOnlyModelViewSet):
    """View cached code feedback"""
    
    queryset = CodeFeedback.objects.all()
    serializer_class = CodeFeedbackSerializer