from fastapi import APIRouter, HTTPException
from typing import List, Any
import json
import io
from contextlib import redirect_stdout, redirect_stderr

from app.schemas import RunRequest, SubmitRequest
from app.utils import normalize_output, extract_stderr_info

router = APIRouter()

LANGUAGE_MAP = {
    "python": 71,
    "javascript": 63,
    "java": 62,
    "cpp": 54,
    "csharp": 51,
    "ruby": 71,
    "go": 60,
    "rust": 73,
}


def execute_python_function(code: str, function_name: str, args: List[Any]):
    """Execute a Python function with given arguments."""
    try:
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        namespace = {}
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, namespace)
        
        if function_name not in namespace:
            return {
                "return_value": None,
                "stdout": stdout_capture.getvalue(),
                "stderr": f"Function '{function_name}' not found in code",
                "success": False
            }
        
        func = namespace[function_name]
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            return_value = func(*args)
        
        return {
            "return_value": return_value,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "success": True
        }
        
    except Exception as e:
        return {
            "return_value": None,
            "stdout": stdout_capture.getvalue() if 'stdout_capture' in locals() else "",
            "stderr": f"{type(e).__name__}: {str(e)}",
            "success": False
        }


def compare_values(actual: Any, expected: Any) -> bool:
    """Compare actual return value with expected value."""
    actual_str = str(actual).strip()
    expected_str = str(expected).strip()
    
    if actual == expected:
        return True
    
    if actual_str == expected_str:
        return True
    
    try:
        if json.dumps(actual, sort_keys=True) == json.dumps(json.loads(expected_str), sort_keys=True):
            return True
    except:
        pass
    
    return False


def extract_function_name(code: str) -> str:
    """Extract function name from code."""
    try:
        if "def " in code:
            parts = code.split("def ")
            if len(parts) > 1:
                func_name = parts[1].split("(")[0].strip()
                if func_name:
                    return func_name
    except:
        pass
    return "solution"


def parse_test_input(test_input: str) -> List[Any]:
    """Parse test input string into arguments list. Handles both old and new formats."""
    args = []
    
    if not test_input:
        return args
    
    try:
        parsed = json.loads(test_input)
        if isinstance(parsed, dict) and 'args' in parsed:
            args = parsed['args']
        elif isinstance(parsed, list):
            args = parsed
        else:
            args = [parsed]
        
        return args
    except json.JSONDecodeError:
        pass

    if test_input:
        parts = [p.strip() for p in test_input.split(",")]
        for p in parts:
            try:
                if "." in p:
                    args.append(float(p))
                else:
                    args.append(int(p))
            except ValueError:
                args.append(p)
    
    return args

@router.post("/run")
async def run_code_api(body: RunRequest):
    """QUICK RUN - Execute code with test case and show PASSED/FAILED"""
    if body.language not in LANGUAGE_MAP:
        raise HTTPException(400, f"Unsupported language: {body.language}")
    
    if body.language != "python":
        raise HTTPException(400, "Currently only Python is supported for /run")
    
    print(f"▶️ [RUN] Language: {body.language}")
    
    try:
        function_name = "solution"
        if "def " in body.code:
            parts = body.code.split("def ")
            if len(parts) > 1:
                func_name = parts[1].split("(")[0].strip()
                if func_name:
                    function_name = func_name
        
        args = []
        test_input = body.stdin or ""
        
        try:
            parsed = json.loads(test_input)
            if isinstance(parsed, list):
                args = parsed
            else:
                args = [parsed]
        except json.JSONDecodeError:
            if test_input:
                parts = [p.strip() for p in test_input.split(",")]
                for p in parts:
                    try:
                        if "." in p:
                            args.append(float(p))
                        else:
                            args.append(int(p))
                    except ValueError:
                        args.append(p)
        
        print(f"   Function: {function_name}")
        print(f"   Args: {args}")
        
       
        if body.expected_output:
            print(f"   Expected: {body.expected_output}")
        
        
        exec_result = execute_python_function(
            code=body.code,
            function_name=function_name,
            args=args
        )
        
        actual_output = str(exec_result["return_value"])
        print(f"   Got: {actual_output}")
        
        # Compare outputs only if expected_output is provided
        passed = False
        if body.expected_output:
            passed = compare_values(exec_result["return_value"], body.expected_output)
        
        if passed:
            print("[RUN] TEST PASSED")
        else:
            print("[RUN] TEST FAILED")
        
        return {
            "stdout": normalize_output(exec_result["stdout"]),
            "stderr": normalize_output(exec_result["stderr"]),
            "actual_output": actual_output,
            "passed": passed,
            "time": 0.01,
            "memory": 0,
            "status": "completed"
        }
        
    except Exception as e:
        print(f"[RUN] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit")
async def submit_code(body: SubmitRequest):
    """SUBMIT SOLUTION - Execute function against all test cases (LeetCode-style)"""
    if body.language not in LANGUAGE_MAP:
        raise HTTPException(400, f"Unsupported language: {body.language}")
    
    if body.language != "python":
        raise HTTPException(400, "Currently only Python is supported for /submit")
    
    if not body.testcases:
        raise HTTPException(400, "No test cases provided")
    
    print("\n [SUBMIT] Starting submission")
    print(f"   Language: {body.language}")
    print(f"   Test cases: {len(body.testcases)}\n")
    
    # Extract function name once
    function_name = extract_function_name(body.code)
    print(f"   Function: {function_name}\n")
    
    final_results = []
    passed_count = 0

    for test_number, tc in enumerate(body.testcases, 1):
        print(f"[SUBMIT] Test {test_number}/{len(body.testcases)}")
        
        try:
            # Parse test input
            args = parse_test_input(tc.input)
            print(f"   Args: {args}")
            
            # Execute function
            exec_result = execute_python_function(
                code=body.code,
                function_name=function_name,
                args=args
            )
            
            actual_output = str(exec_result["return_value"])
            expected_output = str(tc.output)
            
            # Compare outputs
            passed = compare_values(exec_result["return_value"], tc.output)
            
            if passed:
                passed_count += 1
                print("PASSED")
            else:
                print("FAILED")
                print(f"      Expected: {expected_output}")
                print(f"      Got:      {actual_output}")
            
            # Extract error message
            error_msg = None
            if not exec_result["success"]:
                error_msg = exec_result["stderr"]
            elif exec_result["stderr"]:
                error_msg = extract_stderr_info(exec_result["stderr"])
            
            final_results.append({
                "test_number": test_number,
                "input": tc.input,
                "expected_output": expected_output,
                "actual_output": actual_output,
                "passed": passed,
                "error": error_msg
            })

        except Exception as e:
            print(f" Test {test_number}: ERROR - {str(e)}")
            final_results.append({
                "test_number": test_number,
                "input": tc.input,
                "expected_output": tc.output,
                "actual_output": "",
                "passed": False,
                "error": str(e)
            })

    summary = {
        "passed_all": passed_count == len(body.testcases),
        "passed_count": passed_count,
        "total": len(body.testcases),
        "pass_rate": (passed_count / len(body.testcases) * 100) if body.testcases else 0
    }

    print(f"\n [SUBMIT] Summary: {passed_count}/{len(body.testcases)} passed\n")

    return {
        "results": final_results,
        "summary": summary
    }


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}