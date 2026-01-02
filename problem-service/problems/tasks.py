from celery import shared_task
import requests
import json
from .models import Attempt, ExecutionResult, Problem

EXECUTION_SERVICE_URL = "http://execution-service:8005"

def parse_leetcode_input(input_str, function_name):
    """
    Convert LeetCode-style input to execution format.
    
    Input: "10, 15" → {"function_name": "sum_of_two_numbers", "args": [10, 15]}
    Input: "hello, world" → {"function_name": "concat_strings", "args": ["hello", "world"]}
    """
    try:
        parts = [part.strip() for part in input_str.split(',')]
        args = []
        for part in parts:
            try:
                args.append(int(part))
            except ValueError:
                try:
                    args.append(float(part))
                except ValueError:
                    args.append(part)
        
        return {
            "function_name": function_name,
            "args": args
        }
    except Exception as e:
        raise ValueError(f"Failed to parse input '{input_str}': {str(e)}")


@shared_task(bind=True, max_retries=3)
def execute_code_task(self, attempt_id):
    """
    Celery task for LeetCode-style execution with clean display format.
    
    Test cases stored as:
    - input: "10, 15" (clean format for display)
    - output: "25" (clean format)
    
    Converts to JSON format internally for execution-service.
    """
    try:
        print(f"\n{'='*60}")
        print(f"⏳ [Celery] Starting execution for attempt {attempt_id}")
        print(f"{'='*60}\n")
        
        # Fetch attempt from database
        attempt = Attempt.objects.get(id=attempt_id)
        problem = attempt.problem
        
        print(f"[Task] Attempt ID: {attempt.id}")
        print(f"[Task] Problem: {problem.title}")
        print(f"[Task] Language: {attempt.language}")
        print(f"[Task] User ID: {attempt.user_id}\n")
        
        function_name = "solution"
        starter_code = problem.starter_code.get(attempt.language, "")
    
        if "def " in starter_code:
            try:
                func_line = [line for line in starter_code.split('\n') if 'def ' in line][0]
                func_name = func_line.split('def ')[1].split('(')[0].strip()
                function_name = func_name
                print(f"[Task] Detected function name: {function_name}\n")
            except:
                pass
        
        testcases = list(
            problem.testcases.filter(hidden=False)
            .order_by("order")
            .values("input", "output")
        )
        
        print(f"[Task] Found {len(testcases)} public test cases")
        
        if not testcases:
            raise Exception("No public test cases found for this problem")
        
        execution_testcases = []
        for tc in testcases:
            try:
                json_input = parse_leetcode_input(tc["input"], function_name)
                execution_testcases.append({
                    "input": json.dumps(json_input),  
                    "output": tc["output"]
                })
            except ValueError as e:
                print(f"[Task] Error parsing test case: {e}")
                execution_testcases.append({
                    "input": json.dumps({
                        "function_name": function_name,
                        "args": []
                    }),
                    "output": tc["output"]
                })
        
        # Call Execution-Service /submit
        print("[Task] Calling Execution-Service /submit...\n")
        
        response = requests.post(
            f"{EXECUTION_SERVICE_URL}/submit",
            json={
                "code": attempt.code,
                "language": attempt.language,
                "testcases": execution_testcases
            },
            timeout=120  # 2 minutes max
        )
        
        response.raise_for_status()
        exec_data = response.json()
        
        print("[Task] Got response from Execution-Service")
        
        # Extract summary
        summary = exec_data.get("summary", {})
        passed_count = summary.get("passed_count", 0)
        total = summary.get("total", 0)
        
        print(f"[Task] Results: {passed_count}/{total} tests passed")
        print(f"[Task] Pass rate: {summary.get('pass_rate', 0):.1f}%\n")
        
        formatted_results = []
        for result in exec_data.get("results", []):
            try:
                input_json = json.loads(result["input"])
                args = input_json.get("args", [])
                clean_input = ", ".join(str(arg) for arg in args)
            except:
                clean_input = result["input"]
            
            formatted_results.append({
                "test_number": result["test_number"],
                "input": clean_input, 
                "expected_output": result["expected_output"],
                "actual_output": result["actual_output"],
                "passed": result["passed"],
                "error": result.get("error")
            })
        
        
        execution_result = ExecutionResult.objects.create(
            attempt=attempt,
            stdout="",
            stderr="",
            results=formatted_results,  
            passed=summary.get("passed_all", False),
            runtime=0,
            memory=0
        )
        
        print("[Task] Saved ExecutionResult to database")
        print(f"   - Stored {len(formatted_results)} test results\n")
        
        # Update attempt status
        attempt.status = "completed"
        attempt.save()
        
        print("[Task] Attempt marked as 'completed'")
        print(f"{'='*60}")
        print("Task completed successfully!\n")
        print(f"{'='*60}\n")
        
        return {
            "status": "success",
            "attempt_id": attempt_id,
            "passed_all": summary.get("passed_all", False),
            "passed_count": passed_count,
            "total": total,
            "pass_rate": summary.get("pass_rate", 0)
        }
        
    except requests.exceptions.Timeout:
        print("[Task] TIMEOUT: Execution-Service took too long (>120s)")
        attempt = Attempt.objects.get(id=attempt_id)
        attempt.status = "failed"
        attempt.save()
        raise self.retry(exc=Exception("Execution timeout"), countdown=5)
        
    except requests.exceptions.RequestException as e:
        print(f"[Task] REQUEST ERROR: {str(e)}")
        attempt = Attempt.objects.get(id=attempt_id)
        attempt.status = "failed"
        attempt.save()
        raise self.retry(exc=e, countdown=5)
        
    except Attempt.DoesNotExist:
        print(f"[Task] ERROR: Attempt {attempt_id} not found in database")
        return {"status": "failed", "error": "Attempt not found"}
        
    except Exception as e:
        print(f"[Task] UNEXPECTED ERROR: {str(e)}")
        try:
            attempt = Attempt.objects.get(id=attempt_id)
            attempt.status = "failed"
            attempt.save()
        except:
            pass
        raise