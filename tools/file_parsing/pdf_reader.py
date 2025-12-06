"""PDF parsing utility."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pypdf import PdfReader


class PDFReader:
    """Extracts text and metadata from PDF documents."""

    def __init__(self, *, max_pages: int = 25) -> None:
        self.max_pages = max_pages

    def read(
        self,
        path: str,
        *,
        page_slice: Optional[List[int]] = None,
    ) -> Dict[str, object]:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        reader = PdfReader(str(file_path))
        total_pages = len(reader.pages)
        pages_to_read = self._select_pages(total_pages, page_slice)

        extracted_pages: List[Dict[str, object]] = []
        for page_index in pages_to_read[: self.max_pages]:
            page = reader.pages[page_index]
            text = page.extract_text() or ""
            extracted_pages.append({
                "page": page_index + 1,
                "char_count": len(text),
                "text": text,
            })

        metadata = {
            str(k).lstrip("/"): str(v)
            for k, v in (reader.metadata or {}).items()
            if v is not None
        }
        return {
            "path": str(file_path),
            "page_count": total_pages,
            "extracted_pages": extracted_pages,
            "metadata": metadata,
        }

    def _select_pages(self, total_pages: int, page_slice: Optional[List[int]]) -> List[int]:
        if page_slice:
            return [min(total_pages - 1, max(0, page - 1)) for page in page_slice]
        return list(range(total_pages))


if __name__ == "__main__":
    from fpdf import FPDF

    sample_pdf = Path("/tmp/apas_sample.pdf")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "APAS Sample PDF\nThis document tests the PDF reader.")
    pdf.output(str(sample_pdf))

    reader = PDFReader(max_pages=2)
    print(reader.read(str(sample_pdf)))
