from __future__ import annotations

import sys
from pathlib import Path

try:
    from pdfminer.high_level import extract_text
except Exception as exc:  # pragma: no cover
    print("依赖缺失或导入失败，请先安装 pdfminer.six: pip install pdfminer.six")
    raise


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python tools/extract_pdf_text.py <input_pdf> [output_txt]")
        sys.exit(1)

    input_pdf = Path(sys.argv[1]).resolve()
    if not input_pdf.exists():
        print(f"未找到文件: {input_pdf}")
        sys.exit(2)

    output_txt = (
        Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else input_pdf.with_suffix(".txt")
    )

    try:
        text = extract_text(str(input_pdf))
    except Exception as exc:  # pragma: no cover
        print(f"解析失败: {exc}")
        sys.exit(3)

    try:
        output_txt.write_text(text or "", encoding="utf-8")
    except Exception as exc:  # pragma: no cover
        print(f"写入失败: {exc}")
        sys.exit(4)

    print(f"已保存文本至: {output_txt}  (字符数: {len(text or '')})")


if __name__ == "__main__":
    main()


