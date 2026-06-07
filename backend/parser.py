import sys
import json
import os

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

def extract_pdf(filepath):
    if not PdfReader:
        return "PyPDF2 is not installed."
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_docx(filepath):
    if not docx:
        return "python-docx is not installed."
    try:
        doc = docx.Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file paths provided."}))
        sys.exit(1)

    results = []
    
    for filepath in sys.argv[1:]:
        filename = os.path.basename(filepath)
        # Remove the generated prefix "temp_timestamp_" from the original filename if desired,
        # but the Node server can handle that. We just return filename and text.
        text = ""
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.pdf':
            text = extract_pdf(filepath)
        elif ext == '.docx':
            text = extract_docx(filepath)
        else:
            text = "Unsupported file type."
            
        results.append({
            "filename": filename,
            "text": text.strip()
        })
        
    print(json.dumps(results))

if __name__ == "__main__":
    main()
