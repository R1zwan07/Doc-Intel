import fitz
import pdfplumber
import re

class PDFProcessor:
    def extract_text(self, file_path: str) -> str:
        text = ""
        
        # Try PyMuPDF first
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"PyMuPDF error: {e}")
            # Fallback to pdfplumber
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
            except Exception as e2:
                raise Exception(f"Failed to extract text: {e2}")
        
        # Clean text
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()