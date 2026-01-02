from PyPDF2 import PdfReader

def extract_text_from_pdf(file):
    try:
        reader = PdfReader(file)
        text = ""

        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"

        return text.strip()

    except Exception as e:
        print("PDF extraction error:", e)
        return ""
