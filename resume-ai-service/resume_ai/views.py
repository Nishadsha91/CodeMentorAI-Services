from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .utils.pdf_reader import extract_text_from_pdf
from .utils.docx_reader import extract_text_from_docx
from .utils.text_cleaner import clean_resume_text
from resume_ai.ai.enhancer import enhance_resume_text   


class ResumeEnhanceView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get("resume")

        if not file:
            return Response({"error": "No file uploaded"}, status=400)        
        file_type = file.name.split(".")[-1].lower()

        extracted_text = ""

        if file_type == "pdf":
            extracted_text = extract_text_from_pdf(file)
        elif file_type in ["doc", "docx"]:
            extracted_text = extract_text_from_docx(file)
        else:
            return Response({"error": "Unsupported file type"}, status=400)

        if not extracted_text.strip():
            return Response({"error": "Failed to extract text"}, status=422)

        # Clean text
        cleaned_text = clean_resume_text(extracted_text)

        if not cleaned_text.strip():
            return Response({"error": "Resume text is empty after cleaning"}, status=422)

        try:
            enhanced_text = enhance_resume_text(cleaned_text)
        except Exception as e:
            return Response({
                "error": "AI enhancement failed",
                "details": str(e)
            }, status=500)

        #  Return final combined response
        return Response({
            "message": "Resume enhanced successfully",
            "original_text": cleaned_text,
            "enhanced_text": enhanced_text
        }, status=200)
