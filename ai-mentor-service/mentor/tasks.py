from celery import shared_task
from django.utils import timezone
from .models import CodeFeedback, FeedbackRequest
from .gpt_client import gpt_client
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def analyze_code_async(self, request_id: int):
    """
    Async task to get AI feedback on code
    
    Calls GPT-4 API and saves result to DB
    Automatically retries on failure (3 times)
    """
    
    try:
        # Get the request
        request = FeedbackRequest.objects.get(id=request_id)
        request.status = 'processing'
        request.save()
        
        logger.info(f"[CELERY] Processing feedback request {request_id}")
        
        # Check cache first
        code_hash = CodeFeedback.generate_hash(request.code, request.problem_id)
        cached = CodeFeedback.objects.filter(code_hash=code_hash).first()
        
        if cached:
            request.feedback = cached.feedback
            request.scores = cached.scores
            request.interview_ready_score = cached.interview_ready_score
            request.status = "completed"
            request.completed_at = timezone.now()
            request.save()

            return {
                "success": True,
                "request_id": request_id,
                "from_cache": True
            }

        result = gpt_client.get_code_feedback(
            code=request.code,
            problem_description=request.problem_description,
            language=request.language,
            explanation=request.explanation,
            time_taken_seconds=request.time_taken_seconds
        )

        
        if result["success"]:
            scores = result["feedback"]["scores"]

            interview_ready_score = round(
                sum(scores.values()) / len(scores), 2
            )

            CodeFeedback.objects.create(
                code_hash=code_hash,
                code=request.code,
                problem_description=request.problem_description,
                language=request.language,
                problem_id=request.problem_id,
                user_id=request.user_id,
                feedback=result["feedback"],
                scores=scores,
                interview_ready_score=interview_ready_score,
                tokens_used=result["tokens_used"],
            )

            request.feedback = result["feedback"]
            request.scores = scores
            request.interview_ready_score = interview_ready_score
            request.status = "completed"
            request.completed_at = timezone.now()
            request.save()

            
            logger.info(f"[CELERY] Feedback completed for request {request_id} - {result['tokens_used']} tokens")
            
            return {
                'success': True,
                'request_id': request_id,
                'from_cache': False,
                'tokens': result['tokens_used']
            }
        else:
            raise Exception(result['error'])
    
    except FeedbackRequest.DoesNotExist:
        logger.error(f"[CELERY] Request {request_id} not found")
        return {'success': False, 'error': 'Request not found'}
    
    except Exception as e:
        logger.error(f"[CELERY] Error in request {request_id}: {str(e)}")
        
        request = FeedbackRequest.objects.get(id=request_id)
        request.error_message = str(e)
        request.status = 'failed'
        request.save()
    
        raise self.retry(exc=e, countdown=5)