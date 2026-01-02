import os
import json
import requests
from typing import Dict, Optional


class GPTMentorClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_url = os.getenv("GROQ_API")

        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY not set")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_json(self, text: str) -> dict:
        """
        Safely extract first JSON object from model output
        """
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == -1 or end <= start:
            raise ValueError("No valid JSON found in model response")

        return json.loads(text[start:end])

    def get_code_feedback(
        self,
        code: str,
        problem_description: str,
        language: str,
        explanation: str = "",
        time_taken_seconds: Optional[int] = None,
    ) -> Dict:

        prompt = f"""
        ``You are a senior software engineer conducting a real coding interview.

            Return ONLY valid JSON in the following format:

            {{
            "scores": {{
                "correctness": 0-10,
                "efficiency": 0-10,
                "code_quality": 0-10,
                "edge_cases": 0-10,
                "communication": 0-10,
                "engineering_thinking": 0-10
            }},
            "strengths": [],
            "improvements": [],
            "senior_comment": "",
            "next_steps": []
            }}

            Problem:
            {problem_description}

            Language: {language}

            Candidate Explanation:
            {explanation}

            Time Taken (seconds):
            {time_taken_seconds}

            Code:
            {code}

            IMPORTANT:
            - Return ONLY JSON
            - No markdown
            - No extra text
            """

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1200,
        }

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "feedback": None,
                    "tokens_used": None,
                    "error": response.text,
                }

            data = response.json()

            if not data.get("choices"):
                raise ValueError("Groq returned no choices")

            content = data["choices"][0]["message"]["content"].strip()
            feedback = self._extract_json(content)

            return {
                "success": True,
                "feedback": feedback,
                "tokens_used": data.get("usage", {}).get("total_tokens"),
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "feedback": None,
                "tokens_used": None,
                "error": str(e),
            }


gpt_client = GPTMentorClient()
