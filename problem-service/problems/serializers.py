from rest_framework import serializers
from .models import Problem, Attempt, TestCase, ExecutionResult, AIReview


class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ["id", "input", "output", "hidden", "order"]
        read_only_fields = ["id"]


class ProblemSerializer(serializers.ModelSerializer):
    attempted_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = [
            "id", "title", "slug", "difficulty", "category", "acceptance",
            "description", "examples", "starter_code", "constraints", "tags",
            "attempted_by_user",
        ]

    def get_attempted_by_user(self, obj):
        request = self.context.get("request")
        if not request:
            return False

        user_id = request.query_params.get("user_id")
        if not user_id:
            return False

        return obj.attempts.filter(user_id=user_id).exists()


class ProblemDetailSerializer(serializers.ModelSerializer):
    public_testcases = serializers.SerializerMethodField()
    starter_code = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = [
            "id",
            "title",
            "slug",
            "difficulty",
            "category",
            "acceptance",
            "description",
            "examples",
            "starter_code",
            "constraints",
            "public_testcases",
        ]

    def get_starter_code(self, obj):
        return {
            "javascript": obj.starter_code.get("javascript", "// Write your solution here\n"),
            "python": obj.starter_code.get("python", "def solution():\n    pass"),
        }

    def get_public_testcases(self, obj):
        tcs = obj.testcases.filter(hidden=False).order_by("order")
        return [
            {
                "input": tc.input,
                "output": tc.output
            }
            for tc in tcs
        ]


class ExecutionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionResult
        fields = [
            "stdout",
            "stderr",
            "results",
            "passed",
            "runtime",
            "memory",
            "created_at",
        ]


class AIReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIReview
        fields = [
            "scores",
            "summary",
            "full_feedback",
            "suggested_code",
            "created_at",
        ]


class AttemptCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = [
            "id",
            "user_id",
            "problem",
            "code",
            "language",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "status"]


class AttemptSerializer(serializers.ModelSerializer):
    """
    Full attempt response with test results and summary.
    
    THIS IS THE KEY FIX - it extracts 'results' and 'summary' from ExecutionResult
    and returns them so frontend can display detailed test case results.
    """
    execution_result = ExecutionResultSerializer(read_only=True)
    ai_review = AIReviewSerializer(read_only=True)
    results = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = [
            "id",
            "user_id",
            "problem",
            "code",
            "language",
            "status",
            "created_at",
            "updated_at",
            "results",     
            "summary",      
            "execution_result",
            "ai_review",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "execution_result",
            "ai_review",
        ]
    
   
    def get_results(self, obj):
        """
        Extract test case results from ExecutionResult.
        
        The results were already formatted by Execution-Service,
        so just return them as-is.
        """
        if hasattr(obj, 'execution_result') and obj.execution_result:
            return obj.execution_result.results
        return []
    
   
    def get_summary(self, obj):
        """
        Build summary object from execution results.
        
        Calculates: passed_all, passed_count, total, pass_rate
        """
        if hasattr(obj, 'execution_result') and obj.execution_result:
            results = obj.execution_result.results
            total = len(results)
            
            if total == 0:
                return {
                    "passed_all": False,
                    "passed_count": 0,
                    "total": 0,
                    "pass_rate": 0
                }
            
            # Count how many tests passed
            passed_count = sum(1 for r in results if r.get("passed", False))
            
            return {
                "passed_all": obj.execution_result.passed,
                "passed_count": passed_count,
                "total": total,
                "pass_rate": (passed_count / total * 100) if total > 0 else 0
            }
    
        return {
            "passed_all": False,
            "passed_count": 0,
            "total": 0,
            "pass_rate": 0
        }