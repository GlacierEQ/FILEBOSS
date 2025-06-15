import os
import magic # For identifying file types, using pylibmagic
# from winmagic import magic # For python-magic-win64
from PIL import Image # For image processing (OCR)
import pytesseract # For OCR
import PyPDF2 # For PDF text extraction
import docx # For DOCX text extraction
# from .config import Config # If needed for specific paths, though mostly paths come as args

class DocumentProcessor:
    def __init__(self):
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract' # Set if not in PATH in Docker
        # In our Dockerfile, tesseract-ocr is installed, so it should be in PATH.
        pass

    def identify_file_type(self, file_path_on_host):
        """Identifies the file type using python-magic."""
        try:
            mime_type = magic.from_file(file_path_on_host, mime=True)
            return mime_type
        except Exception as e:
            print(f"Error identifying file type for {file_path_on_host}: {e}")
            # Fallback to extension if magic fails, though less reliable
            _, ext = os.path.splitext(file_path_on_host)
            return ext.lower()

    def extract_text_from_pdf(self, pdf_file_path):
        """Extracts text from a PDF file."""
        text = ""
        try:
            with open(pdf_file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() if page.extract_text() else ""
            print(f"Extracted text from PDF: {pdf_file_path} (first 100 chars: {text[:100]}...)")
            return text
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_file_path}: {e}")
            return ""

    def extract_text_from_docx(self, docx_file_path):
        """Extracts text from a DOCX file."""
        text = ""
        try:
            doc = docx.Document(docx_file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
            print(f"Extracted text from DOCX: {docx_file_path} (first 100 chars: {text[:100]}...)")
            return text
        except Exception as e:
            print(f"Error extracting text from DOCX {docx_file_path}: {e}")
            return ""

    def extract_text_from_image_ocr(self, image_file_path):
        """Extracts text from an image file using Tesseract OCR."""
        text = ""
        try:
            # You might want to specify language(s) for Tesseract if not English
            # e.g., text = pytesseract.image_to_string(Image.open(image_file_path), lang='eng+fra')
            text = pytesseract.image_to_string(Image.open(image_file_path))
            print(f"Extracted text from Image (OCR): {image_file_path} (first 100 chars: {text[:100]}...)")
            return text
        except Exception as e:
            print(f"Error performing OCR on image {image_file_path}: {e}")
            return ""

    def process_document(self, file_path_on_host):
        """
        Processes a document file, extracting text based on its type.
        file_path_on_host: Absolute path to the document on the legal_brain_service container's filesystem.
        """
        if not os.path.exists(file_path_on_host):
            return {"error": "File not found", "file_path": file_path_on_host}

        mime_type = self.identify_file_type(file_path_on_host)
        print(f"Identified MIME type for {file_path_on_host}: {mime_type}")
        
        extracted_text = ""
        file_type_processed = "unknown"

        if "pdf" in mime_type:
            extracted_text = self.extract_text_from_pdf(file_path_on_host)
            file_type_processed = "pdf"
        elif "officedocument.wordprocessingml.document" in mime_type or file_path_on_host.endswith(".docx"): # Check extension as fallback
            extracted_text = self.extract_text_from_docx(file_path_on_host)
            file_type_processed = "docx"
        elif mime_type.startswith("image/"):
            # Common image types: image/jpeg, image/png, image/tiff, image/bmp, image/gif
            # Tesseract supports many of these.
            extracted_text = self.extract_text_from_image_ocr(file_path_on_host)
            file_type_processed = "image_ocr"
        else:
            # Could add more types like .txt, .rtf, etc.
            print(f"Unsupported or unrecognized document type for {file_path_on_host} (MIME: {mime_type}).")
            return {"error": "Unsupported document type", "file_path": file_path_on_host, "mime_type": mime_type}

        return {
            "file_path": file_path_on_host,
            "file_type": file_type_processed,
            "mime_type": mime_type,
            "extracted_text_preview": extracted_text[:200] + "..." if extracted_text else "No text extracted.",
            "full_text": extracted_text # Consider if sending full text in every response is wise for large docs
        }

# Example Usage (for testing this module directly)
if __name__ == '__main__':
    processor = DocumentProcessor()

    # For testing, you'd need some sample files.
    # Create dummy files for path testing if real ones aren't available.
    # Ensure Tesseract is installed and configured if testing OCR.
    
    sample_files_dir = "./sample_docs_for_testing"
    os.makedirs(sample_files_dir, exist_ok=True)

    # Dummy PDF (not a real PDF, just for path testing)
    dummy_pdf_path = os.path.join(sample_files_dir, "test.pdf")
    if not os.path.exists(dummy_pdf_path):
        with open(dummy_pdf_path, "w") as f: f.write("dummy pdf content")
        print(f"Created dummy file: {dummy_pdf_path}")
    
    # Dummy DOCX (not a real DOCX)
    dummy_docx_path = os.path.join(sample_files_dir, "test.docx")
    if not os.path.exists(dummy_docx_path):
        with open(dummy_docx_path, "w") as f: f.write("dummy docx content")
        print(f"Created dummy file: {dummy_docx_path}")

    # Dummy Image (not a real image)
    dummy_image_path = os.path.join(sample_files_dir, "test.png")
    if not os.path.exists(dummy_image_path):
        with open(dummy_image_path, "w") as f: f.write("dummy image content")
        print(f"Created dummy file: {dummy_image_path}")

    test_files = [dummy_pdf_path, dummy_docx_path, dummy_image_path]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\nProcessing document: {test_file}")
            # Note: These dummy files will likely fail actual text extraction
            # as they are not valid file formats. This tests the processing flow.
            result = processor.process_document(test_file)
            print("Processing Result:")
            # Print relevant parts of the result, avoid huge text dumps
            preview = result.get("extracted_text_preview", result.get("error", "Unknown error"))
            print(f"  File: {result.get('file_path')}")
            print(f"  Type: {result.get('file_type', 'N/A')}")
            print(f"  MIME: {result.get('mime_type', 'N/A')}")
            print(f"  Preview/Error: {preview}")
        else:
            print(f"\nTest file not found: {test_file}")
