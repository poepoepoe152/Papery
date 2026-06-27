"""Text extraction with automatic OCR fallback.

- Digital PDFs: extract the text layer directly (PyMuPDF).
- Scanned PDFs / images: OCR via Tesseract (PaddleOCR is the production engine;
  Tesseract is the bundled fallback from the architecture's OCR chain).
- DOCX: read paragraphs and tables.

OCR degrades gracefully: if the Tesseract binary is unavailable, extraction
still returns whatever digital text exists rather than raising.
"""
import io
import os

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}


def _ocr_image(image) -> str:
    try:
        import pytesseract

        return pytesseract.image_to_string(image)
    except Exception as exc:  # noqa: BLE001 - missing binary or runtime error
        print(f"[ocr] skipped: {exc}")
        return ""


def _extract_pdf(path: str) -> tuple[str, int]:
    import fitz  # PyMuPDF

    parts: list[str] = []
    with fitz.open(path) as doc:
        page_count = doc.page_count
        for page in doc:
            text = page.get_text("text")
            if len(text.strip()) < 20:
                # Likely a scanned page -> rasterize and OCR.
                try:
                    from PIL import Image

                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    text = _ocr_image(img)
                except Exception as exc:  # noqa: BLE001
                    print(f"[ocr] page render failed: {exc}")
            parts.append(text)
    return "\n".join(parts), page_count


def _extract_docx(path: str) -> tuple[str, int]:
    import docx

    document = docx.Document(path)
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append("\t".join(cell.text for cell in row.cells))
    return "\n".join(parts), 1


def _extract_image(path: str) -> tuple[str, int]:
    from PIL import Image

    with Image.open(path) as img:
        return _ocr_image(img), 1


def extract_text(path: str, original_name: str = "") -> dict:
    """Return {text, page_count, engine}."""
    ext = os.path.splitext(original_name or path)[1].lower()
    try:
        if ext == ".pdf":
            text, pages = _extract_pdf(path)
            engine = "PDF/OCR"
        elif ext == ".docx":
            text, pages = _extract_docx(path)
            engine = "DOCX"
        elif ext in _IMAGE_EXTS:
            text, pages = _extract_image(path)
            engine = "OCR"
        else:
            text, pages, engine = "", 0, "UNSUPPORTED"
    except Exception as exc:  # noqa: BLE001
        print(f"[extract] failed for {original_name}: {exc}")
        text, pages, engine = "", 0, "ERROR"

    return {"text": text or "", "page_count": pages, "engine": engine}
