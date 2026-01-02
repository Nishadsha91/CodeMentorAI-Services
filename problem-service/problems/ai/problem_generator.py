import requests
from pathlib import Path
import json
import os
import environ
import re
import time

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

API_URL = env("AI_PROBLEM_API")
API_KEY = env("AI_API_KEY")

def generate_problem(difficulty, topic):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # only numeric/string args
    instructions = f"""
    Return ONLY this JSON with double quotes:   

    {{"title":"Problem","description":"Description","function_name":"func_name",
    "examples":[{{"input":"1, 2","output":"3","explanation":"text"}}],
    "test_cases":[{{"args":[1,2],"output":"3"}},{{"args":[0,0],"output":"0"}},{{"args":[5,5],"output":"10"}}],
    "starter_code":{{"python":"def func_name(a,b): pass"}},"constraints":["constraint"],"tags":["tag"]}}

    Make it about {difficulty} level {topic} problem. Use simple integer or string args only. NO dictionaries, NO lists as args, NO complex structures. Output as JSON only."""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Output ONLY valid JSON. No markdown, no text, no explanations. Use double quotes only."},
            {"role": "user", "content": instructions},
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }

    try:
        # delay to avoid rate limiting
        time.sleep(1)
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        response_data = response.json()
        
        if "error" in response_data:
            raise Exception(f"API Error: {response_data['error'].get('message', 'Unknown')}")
        
        if "choices" not in response_data or len(response_data["choices"]) == 0:
            raise Exception("No choices in response")
        
        content = response_data["choices"][0]["message"]["content"].strip()
        content = content.replace("```json", "").replace("```", "")
        
        start = content.find('{')
        end = content.rfind('}') + 1
        
        if start < 0 or end <= start:
            raise Exception("No JSON found in response")
        
        content = content[start:end]
        
        content = re.sub(r"([^\\])'", r'\1"', content)  
        content = content.replace("'", '"')          
        content = re.sub(r':\s*\[', ': [', content)  
        
        # Parse and validate
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            # Last resort - try to extract just the JSON structure we need
            print("[AI] JSON decode failed, using fallback")
            data = {
                "title": "Problem",
                "description": "Solve this problem",
                "function_name": "solution",
                "examples": [{"input": "example", "output": "output", "explanation": "explanation"}],
                "test_cases": [],
                "starter_code": {"python": "def solution(): pass"},
                "constraints": [],
                "tags": []
            }
        
        data.setdefault("title", "Problem")
        data.setdefault("function_name", "solution")
        data.setdefault("description", "Solve this problem")
        data.setdefault("test_cases", [])
        data.setdefault("examples", [])
        data.setdefault("starter_code", {"python": "def solution(): pass"})
        data.setdefault("constraints", [])
        data.setdefault("tags", [])
        
        return data
        
    except requests.exceptions.Timeout:
        raise Exception("Request timeout - API took too long")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {str(e)[:50]}")
    except Exception as e:
        raise Exception(f"{str(e)[:100]}")
    