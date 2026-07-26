"""
V3: OCR 文本提取（tesseract）。

业务方安装：apt-get install tesseract-ocr tesseract-ocr-chi-sim
Python：pip install pytesseract pillow

业务方 yaml：
  ocr: tesseract
  ocr_lang: chi_sim+eng
"""
from __future__ import annotations

from pathlib import Path


def ocr_image(image_path: Path, lang: str = "chi_sim+eng") -> str:
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        return ""
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img, lang=lang).strip()
    except Exception as e:                                  # noqa: BLE001
        print(f"[ocr] failed on {image_path}: {e}")
        return ""


def ocr_pdf_pages(pdf_path: Path, lang: str = "chi_sim+eng") -> str:
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return ""
    try:
        images = convert_from_path(str(pdf_path))
        chunks = []
        for i, img in enumerate(images):
            tmp = pdf_path.with_suffix(f".ocr_p{i}.png")
            img.save(tmp)
            txt = ocr_image(tmp, lang=lang)
            chunks.append(f"\n[Page {i+1}]\n{txt}")
            tmp.unlink()
        return "\n".join(chunks).strip()
    except Exception as e:                                  # noqa: BLE001
        print(f"[ocr_pdf] failed on {pdf_path}: {e}")
        return ""