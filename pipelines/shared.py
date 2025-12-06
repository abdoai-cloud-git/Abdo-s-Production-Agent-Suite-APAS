"""Shared helpers for pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel

from tools.file_parsing import CSVReader, CSVReaderConfig, ImageReader, PDFReader


class ReferenceFile(BaseModel):
    path: str
    type: Literal["csv", "pdf", "image"]
    description: str = ""


class ReferenceIngestor:
    def __init__(
        self,
        *,
        csv_reader: Optional[CSVReader] = None,
        pdf_reader: Optional[PDFReader] = None,
        image_reader: Optional[ImageReader] = None,
    ) -> None:
        self.csv_reader = csv_reader or CSVReader(CSVReaderConfig(max_rows=500))
        self.pdf_reader = pdf_reader or PDFReader(max_pages=10)
        self.image_reader = image_reader or ImageReader()

    def ingest(self, references: List[ReferenceFile], *, perform_ocr: bool = True) -> List[str]:
        digests: List[str] = []
        for ref in references:
            path = Path(ref.path)
            try:
                if ref.type == "csv":
                    parsed = self.csv_reader.read(str(path), limit=50)
                    digests.append(
                        f"CSV:{path.name} columns={parsed['columns']} sample={parsed['rows'][:2]}"
                    )
                elif ref.type == "pdf":
                    parsed = self.pdf_reader.read(str(path))
                    snippet = (
                        parsed["extracted_pages"][0]["text"][:300]
                        if parsed["extracted_pages"]
                        else ""
                    )
                    digests.append(
                        f"PDF:{path.name} pages={parsed['page_count']} snippet={snippet}"
                    )
                elif ref.type == "image":
                    parsed = self.image_reader.read(str(path), perform_ocr=perform_ocr)
                    digests.append(
                        f"IMAGE:{path.name} meta={parsed['metadata']} ocr={parsed['ocr_text'][:200]}"
                    )
            except FileNotFoundError:
                digests.append(f"{ref.type.upper()}:{path.name} missing; skipped.")
        return digests
