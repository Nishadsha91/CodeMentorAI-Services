# resume_ai/ai/enhancer.py

from .prompts import build_resume_prompt
from .clients.groq_client import call_groq

def enhance_resume_text(resume_text: str) -> str:
    """
    Takes extracted resume text, builds prompt, sends to Groq LLaMA,
    and returns the improved resume content.
    """
    prompt = build_resume_prompt(resume_text)

    enhanced_text = call_groq(prompt)
    return enhanced_text
