from io import BytesIO
import fitz
from docx import Document

def extract_text(uploaded) -> str:
    suffix = uploaded.name.rsplit(".", 1)[-1].lower()
    data = uploaded.getvalue()
    if suffix == "txt": return data.decode("utf-8", errors="ignore")
    if suffix == "pdf": return "\n".join(page.get_text() for page in fitz.open(stream=data, filetype="pdf"))
    if suffix == "docx":
        return "\n".join(p.text for p in Document(BytesIO(data)).paragraphs)
    raise ValueError("Upload a PDF, DOCX, or TXT file.")
