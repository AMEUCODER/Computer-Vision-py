"""DOCX to PDF conversion (requires Microsoft Word on Windows/macOS)."""
from __future__ import annotations
import argparse
from pathlib import Path


def convert_word_to_pdf(input_docx: str, output_pdf: str | None = None) -> Path:
    try:
        from docx2pdf import convert
    except ImportError as exc:
        raise RuntimeError("Install docx2pdf with: python -m pip install docx2pdf") from exc
    source = Path(input_docx).expanduser()
    if not source.is_file():
        raise FileNotFoundError(source)
    destination = Path(output_pdf).expanduser() if output_pdf else source.with_suffix(".pdf")
    destination.parent.mkdir(parents=True, exist_ok=True)
    convert(str(source), str(destination))
    if not destination.is_file():
        raise RuntimeError("Conversion did not create a PDF. docx2pdf requires Microsoft Word.")
    return destination


def main():
    parser = argparse.ArgumentParser(description="Convert Word DOCX to PDF")
    parser.add_argument("input")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()
    print(f"Saved: {convert_word_to_pdf(args.input, args.output)}")


if __name__ == "__main__":
    main()
