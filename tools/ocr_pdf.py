from __future__ import annotations

import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception:
    print("请先安装 pymupdf：pip install pymupdf")
    raise


def extract_text_by_pymupdf(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    texts: list[str] = []
    for i in range(len(doc)):
        page = doc[i]
        txt = page.get_text("text") or ""
        texts.append(txt)
    return "\n".join(texts).strip()


def ocr_pdf_to_text(pdf_path: Path) -> str:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception:
        print("如需 OCR，请先安装：pip install rapidocr-onnxruntime pillow")
        raise

    ocr = RapidOCR()
    doc = fitz.open(str(pdf_path))
    parts: list[str] = []
    for i in range(len(doc)):
        page = doc[i]
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        result, _ = ocr(img_bytes)
        if result:
            parts.append(" ".join([line[1] for line in result]))
    return "\n".join(parts).strip()


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python tools/ocr_pdf.py <input_pdf> [output_txt]")
        sys.exit(1)

    input_pdf = Path(sys.argv[1]).resolve()
    if not input_pdf.exists():
        print(f"未找到文件: {input_pdf}")
        sys.exit(2)

    output_txt = (
        Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else input_pdf.with_name(input_pdf.stem + "_ocr.txt")
    )

    text = extract_text_by_pymupdf(input_pdf)
    if not text or len(text.replace("\n", "").strip()) < 10:
        print("直接文本提取内容很少，尝试 OCR……")
        text = ocr_pdf_to_text(input_pdf)

    output_txt.write_text(text or "", encoding="utf-8")
    print(f"已保存文本至: {output_txt} (字符数: {len(text or '')})")


if __name__ == "__main__":
    main()





