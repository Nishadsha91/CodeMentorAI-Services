from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Attempt, Problem, ExecutionResult, TestCase  # noqa: F401
from .serializers import ProblemDetailSerializer, ProblemSerializer, AttemptCreateSerializer, AttemptSerializer
from django_filters.rest_framework import DjangoFilterBackend
from problems.events.publisher import publish_event
from .tasks import execute_code_task
import requests
import time  # noqa: F401


class ProblemListView(generics.ListAPIView):
    """List all problems with filtering and search"""
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["difficulty", "category"]  
    search_fields = ["title", "description"]


class ProblemDetailView(generics.RetrieveAPIView):
    """Get problem details"""
    queryset = Problem.objects.all()
    serializer_class = ProblemDetailSerializer  
    lookup_field = "slug"


class CreateAttemptView(APIView):
    """Save a quick attempt without executing"""
    def post(self, request, slug):
        problem = get_object_or_404(Problem, slug=slug)

        serializer = AttemptCreateSerializer(data={
            "user_id": request.data.get("user_id", 1),
            "problem": problem.id,
            "code": request.data.get("code", ""),
            "language": request.data.get("language", "")
        })

        serializer.is_valid(raise_exception=True)
        attempt = serializer.save()

        publish_event("problem_attempted", {
            "event": "problem.attempted",
            "user_id": attempt.user_id,
            "problem_title": problem.title,
            "slug": problem.slug,
            "difficulty": problem.difficulty,
        })

        return Response(
            AttemptCreateSerializer(attempt).data,
            status=status.HTTP_201_CREATED
        )


class AttemptDetailView(APIView):
    """Get attempt details with execution results"""
    def get(self, request, attempt_id):
        attempt = get_object_or_404(Attempt, id=attempt_id)
        return Response(AttemptSerializer(attempt).data)


class RunCodeView(APIView):
    """
    QUICK RUN - Execute code with custom input (stdin)
    
    No test cases, no saving Attempt record.
    Synchronous - user waits for output.
    Direct call to Execution-Service.
    
    Flow: Frontend → Problem-Service → Execution-Service → Judge0 → Back
    """
    EXECUTION_URL = "http://execution-service:8005/run"
    
    def post(self, request, slug):
        code = request.data.get("code")
        language = request.data.get("language")
        stdin = request.data.get("stdin", "")
        
        if not code or not language:
            return Response(
                {"error": "Both 'code' and 'language' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"[RUN] Quick execution - Language: {language}")
        
        try:
            res = requests.post(
                self.EXECUTION_URL,
                json={
                    "code": code,
                    "language": language,
                    "stdin": stdin
                },
                timeout=35
            )
            
            res.raise_for_status()
            data = res.json()
            
            print("[RUN] Quick execution completed")
            return Response(data, status=status.HTTP_200_OK)
            
        except requests.exceptions.Timeout:
            return Response(
                {"error": "Execution timeout - code took too long to run"},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Execution service error: {str(e)}"}, 
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubmitAttemptView(APIView):
    """
    SUBMIT SOLUTION - Execute code against all test cases
    
    Uses Celery for async execution with synchronous response.
    
    Flow:
    1. Create Attempt record
    2. Send to Celery task queue (async via RabbitMQ)
    3. WAIT for Celery result (blocking)
    4. Execution-Service processes code
    5. Results saved to database
    6. Return results to Frontend
    
    Frontend sees: Simple submit → wait → get results
    Backend does: Async execution, sync response pattern
    """
    
    def post(self, request, slug):
        problem = get_object_or_404(Problem, slug=slug)
        
        print(f"[SUBMIT] Received submission for problem: {slug}")
        
        attempt_serializer = AttemptCreateSerializer(data={
            "user_id": request.data.get("user_id", 1),
            "problem": problem.id,
            "code": request.data.get("code"),
            "language": request.data.get("language"),
        })
        
        attempt_serializer.is_valid(raise_exception=True)
        attempt = attempt_serializer.save(status="running")
        
        print(f"[SUBMIT] Created attempt record: {attempt.id}")
        print("[SUBMIT] Sending to Celery task queue...")
        
        task = execute_code_task.delay(attempt.id)
        
        print(f"[SUBMIT] Task queued with ID: {task.id}")
        
        print("[SUBMIT] Waiting for execution to complete...")
        
        try:
            result = task.get(timeout=60)
            print(f"[SUBMIT] Task completed: {result}")
        except Exception as e:
            print(f"[SUBMIT] Task failed or timed out: {str(e)}")
            attempt.status = "failed"
            attempt.save()
            return Response(
                {"error": f"Execution failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        attempt.refresh_from_db()
        
        print("[SUBMIT] Returning results to frontend")
        
        return Response(
            AttemptSerializer(attempt).data,
            status=status.HTTP_200_OK
        )