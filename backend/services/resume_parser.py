from pathlib import Path
import fitz
from docx import Document
from fastapi import HTTPException, UploadFile
from .text_cleaner import clean_text

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024


async def parse_upload(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {file.filename}. Use PDF, DOCX, or TXT.")
    data = await file.read()
    if not data:
        raise HTTPException(400, f"{file.filename} is empty.")
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(400, f"{file.filename} exceeds the 5 MB file limit.")
    try:
        if suffix == ".txt":
            text = data.decode("utf-8", errors="replace")
        elif suffix == ".pdf":
            doc = fitz.open(stream=data, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
        else:
            from io import BytesIO
            text = "\n".join(p.text for p in Document(BytesIO(data)).paragraphs)
    except Exception as exc:
        raise HTTPException(400, f"Could not read {file.filename}: document may be corrupted.") from exc
    text = clean_text(text)
    if len(text) < 15:
        raise HTTPException(400, f"{file.filename} contains little or no extractable text.")
    return text


def parse_path(path: Path) -> str:
    """Test/sample convenience parser."""
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return clean_text(path.read_text(encoding="utf-8"))
    raise ValueError("parse_path supports text samples only")
