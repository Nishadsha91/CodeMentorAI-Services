import docx

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()

    except Exception as e:
        print("DOCX extraction error:", e)
        return ""
