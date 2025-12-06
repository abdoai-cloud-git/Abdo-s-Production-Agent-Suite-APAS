"""Image parsing utility with optional OCR."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from PIL import Image, ImageStat

try:  # pragma: no cover - optional dependency
    import pytesseract
    from pytesseract import TesseractError
except ImportError:  # pragma: no cover - allow graceful degradation
    pytesseract = None
    TesseractError = RuntimeError


class ImageReader:
    """Extracts metadata and OCR text from images."""

    def __init__(self, *, max_dimension: int = 2000) -> None:
        self.max_dimension = max_dimension

    def read(
        self,
        path: str,
        *,
        perform_ocr: bool = True,
        languages: str = "eng",
    ) -> Dict[str, object]:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image not found: {file_path}")

        with Image.open(file_path) as img:
            metadata = self._metadata(img)
            text = ""
            warnings = []
            if perform_ocr:
                text, warning = self._ocr(img, languages)
                if warning:
                    warnings.append(warning)

        return {
            "path": str(file_path),
            "metadata": metadata,
            "ocr_text": text.strip(),
            "warnings": warnings,
        }

    def _metadata(self, img: Image.Image) -> Dict[str, object]:
        width, height = img.size
        stats = ImageStat.Stat(img.convert("RGB"))
        return {
            "width": width,
            "height": height,
            "mode": img.mode,
            "format": img.format,
            "average_rgb": [round(value, 2) for value in stats.mean],
            "dpi": img.info.get("dpi"),
        }

    def _ocr(self, img: Image.Image, languages: str) -> tuple[str, Optional[str]]:
        if pytesseract is None:
            return "", "pytesseract not installed; OCR skipped"

        resized = self._prepare_for_ocr(img)
        try:
            return pytesseract.image_to_string(resized, lang=languages), None
        except TesseractError as exc:
            return "", f"OCR failed: {exc}"

    def _prepare_for_ocr(self, img: Image.Image) -> Image.Image:
        width, height = img.size
        scale = min(self.max_dimension / max(width, height), 1)
        if scale < 1:
            new_size = (int(width * scale), int(height * scale))
            return img.resize(new_size, Image.Resampling.LANCZOS)
        return img


if __name__ == "__main__":
    from PIL import ImageDraw

    sample_path = Path("/tmp/apas_sample.png")
    image = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((10, 80), "APAS", fill=(0, 0, 0))
    image.save(sample_path)

    reader = ImageReader()
    print(reader.read(str(sample_path), perform_ocr=False))
