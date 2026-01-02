# resume_ai/ai/prompts.py

# 1. SYSTEM ROLE (WHO the AI should behave as)
SYSTEM_PROMPT = """
You are an expert resume writer and ATS optimization specialist.
Your job is to rewrite resumes professionally while keeping meaning intact.
You improve clarity, grammar, impact, and relevance to modern hiring standards.
Use strong action verbs and concise bullet points.
Keep formatting clean and professional.
"""

# 2. MAIN INSTRUCTION TEMPLATE
INSTRUCTION_TEMPLATE = """
Rewrite the following resume content in a more clear, professional,
ATS-friendly format. Improve grammar, clarity, and impact.

Requirements:
- Use concise bullet points.
- Highlight important technical/soft skills.
- Remove redundancy.
- Keep meaning accurate.
- Improve formatting.
- Make it recruiter-friendly.
- DO NOT add fake experience.
- DO NOT invent details that are not present.

Here is the resume content to enhance:

---
{resume_text}
---
"""

# 3. FUNCTION TO BUILD FINAL PROMPT FOR LLaMA
def build_resume_prompt(resume_text: str) -> str:
    """
    Constructs the final prompt sent to the AI model.
    Combines system role + instructions + actual resume content.
    """
    prompt = SYSTEM_PROMPT + "\n" + INSTRUCTION_TEMPLATE.format(resume_text=resume_text)
    return prompt.strip()
