import re

def clean_resume_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace("\n", " ").strip()
    return text
