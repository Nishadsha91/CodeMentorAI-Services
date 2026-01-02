import os
import asyncio
import httpx

JUDGE0_BASE_URL = os.getenv("JUDGE0_BASE_URL")  
JUDGE0_API_KEY = os.getenv("JUDGE0_API_KEY") 
JUDGE0_TIMEOUT = int(os.getenv("JUDGE0_TIMEOUT", "30"))

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": JUDGE0_API_KEY,
    "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
}

class Judge0Client:
    async def create_submission(self, code, language_id, stdin=""):
        """Create a submission and return token"""
        payload = {
            "source_code": code,
            "language_id": language_id,
            "stdin": stdin or "",
        }

        params = {
            "base64_encoded": "false",
            "wait": "false" 
        }

        print(f"[DEBUG] Creating submission at: {JUDGE0_BASE_URL}/submissions")
        print(f"[DEBUG] Language ID: {language_id}")
        print(f"[DEBUG] Code length: {len(code)}")
        
        try:
            async with httpx.AsyncClient(timeout=JUDGE0_TIMEOUT) as client:
                r = await client.post(
                    f"{JUDGE0_BASE_URL}/submissions",
                    json=payload,
                    params=params,
                    headers=DEFAULT_HEADERS,
                )
                
                print(f"[DEBUG] Response Status: {r.status_code}")
                
                if r.status_code not in [200, 201]:
                    print(f"[ERROR] Judge0 returned error: {r.status_code}")
                    print(f"[ERROR] Response: {r.text}")
                    return None
                
                response_data = r.json()
                token = response_data.get("token")
                print(f"[SUCCESS] Submission created with token: {token}")
                return token
                
        except Exception as e:
            print(f"[ERROR] Exception in create_submission: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def get_submission_result(self, token):
        """Poll for submission result"""
        print(f"[DEBUG] Polling for result with token: {token}")
        
        for attempt in range(20): 
            try:
                await asyncio.sleep(1)
                
                async with httpx.AsyncClient(timeout=JUDGE0_TIMEOUT) as client:
                    r = await client.get(
                        f"{JUDGE0_BASE_URL}/submissions/{token}",
                        headers=DEFAULT_HEADERS,
                    )
                    
                if r.status_code == 200:
                    result = r.json()
                    status_id = result.get("status", {}).get("id", 1)
                    
                    print(f"[DEBUG] Attempt {attempt + 1}: Status ID = {status_id}")
                    
                    if status_id > 2:
                        print(f"[SUCCESS] Execution completed with status: {result.get('status', {}).get('description')}")
                        return result
                    else:
                        print("[INFO] Still processing...")
                else:
                    print(f"[WARNING] GET request failed: {r.status_code}")
                    
            except Exception as e:
                print(f"[WARNING] Error polling attempt {attempt + 1}: {e}")
        
        print("[ERROR] Timeout waiting for result")
        return None

    async def run_code(self, code, language_id, stdin=""):
        """Main method to run code"""

        print("=== Starting code execution ===")
        print(f"Language ID: {language_id}")
        
        token = await self.create_submission(code, language_id, stdin)
        
        if not token:
            print("[ERROR] Failed to create submission")
            return {
                "stdout": "",
                "stderr": "Failed to create submission",
                "time": 0,
                "memory": 0,
                "status": {"id": 13, "description": "Internal Error"}
            }
        
        result = await self.get_submission_result(token)
        
        if not result:
            print("[ERROR] Failed to get result")
            return {
                "stdout": "",
                "stderr": "Timeout waiting for execution result",
                "time": 0,
                "memory": 0,
                "status": {"id": 13, "description": "Timeout"}
            }
        
        return {
            "stdout": result.get("stdout") or "",
            "stderr": result.get("stderr") or "",
            "time": result.get("time") or 0,
            "memory": result.get("memory") or 0,
            "status": result.get("status") or {"id": 13, "description": "Unknown"}
        }


judge0_client = Judge0Client()