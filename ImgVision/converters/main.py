"""ImgVision document converters: images to PDF, PDF to images, and PDF to Word."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def images_to_pdf(inputs: list[str], output: str) -> Path:
    """Combine one or more images into a single PDF."""
    paths = [Path(p).expanduser() for p in inputs]
    if not paths:
        raise ValueError("Select at least one image.")
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")
        if path.suffix.lower() not in IMAGE_EXTS:
            raise ValueError(f"Unsupported image format: {path.suffix}")
    try:
        import img2pdf
    except ImportError as exc:
        raise RuntimeError("Missing dependency. Install with: python -m pip install -r requirements-converters.txt") from exc

    destination = Path(output).expanduser()
    if destination.suffix.lower() != ".pdf":
        destination = destination.with_suffix(".pdf")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as pdf_file:
        pdf_file.write(img2pdf.convert([str(p) for p in paths]))
    return destination


def pdf_to_images(input_pdf: str, output_dir: str, dpi: int = 200, image_format: str = "png") -> list[Path]:
    """Render every PDF page as an image using PyMuPDF (no Poppler required)."""
    source = Path(input_pdf).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"PDF not found: {source}")
    if source.suffix.lower() != ".pdf":
        raise ValueError("Input must be a PDF file.")
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("Missing dependency. Install with: python -m pip install -r requirements-converters.txt") from exc
    if dpi < 36 or dpi > 1200:
        raise ValueError("DPI must be between 36 and 1200.")
    fmt = image_format.lower()
    if fmt not in {"png", "jpg", "jpeg"}:
        raise ValueError("Image format must be png or jpg.")

    destination = Path(output_dir).expanduser()
    destination.mkdir(parents=True, exist_ok=True)
    saved = []
    with fitz.open(source) as document:
        if document.needs_pass:
            raise ValueError("This PDF is password-protected.")
        scale = dpi / 72
        matrix = fitz.Matrix(scale, scale)
        for index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            suffix = "jpg" if fmt == "jpeg" else fmt
            target = destination / f"{source.stem}_page_{index:03d}.{suffix}"
            pixmap.save(str(target))
            saved.append(target)
    return saved


def pdf_to_word(input_pdf: str, output_docx: str) -> Path:
    """Convert a PDF into an editable DOCX document."""
    source = Path(input_pdf).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"PDF not found: {source}")
    if source.suffix.lower() != ".pdf":
        raise ValueError("Input must be a PDF file.")
    try:
        from pdf2docx import Converter
    except ImportError as exc:
        raise RuntimeError("Missing dependency. Install with: python -m pip install -r requirements-converters.txt") from exc
    destination = Path(output_docx).expanduser()
    if destination.suffix.lower() != ".docx":
        destination = destination.with_suffix(".docx")
    destination.parent.mkdir(parents=True, exist_ok=True)

    converter = Converter(str(source))
    try:
        converter.convert(str(destination), start=0, end=None)
    finally:
        converter.close()
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="imgvision-convert", description="ImgVision file converters")
    commands = parser.add_subparsers(dest="command", required=True)

    to_pdf = commands.add_parser("img2pdf", help="Combine images into one PDF")
    to_pdf.add_argument("images", nargs="+", help="Input image(s), in page order")
    to_pdf.add_argument("-o", "--output", required=True, help="Output PDF path")

    to_img = commands.add_parser("pdf2img", help="Render PDF pages as images")
    to_img.add_argument("pdf", help="Input PDF")
    to_img.add_argument("-o", "--output", default="pdf_pages", help="Output folder")
    to_img.add_argument("--dpi", type=int, default=200, help="Render resolution (36–1200)")
    to_img.add_argument("--format", choices=["png", "jpg", "jpeg"], default="png")

    to_word = commands.add_parser("pdf2word", help="Convert PDF to editable Word DOCX")
    to_word.add_argument("pdf", help="Input PDF")
    to_word.add_argument("-o", "--output", help="Output DOCX path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "img2pdf":
            result = images_to_pdf(args.images, args.output)
            print(f"Saved PDF: {result}")
        elif args.command == "pdf2img":
            results = pdf_to_images(args.pdf, args.output, args.dpi, args.format)
            print(f"Saved {len(results)} page image(s) to: {Path(args.output).expanduser()}")
        elif args.command == "pdf2word":
            output = args.output or str(Path(args.pdf).with_suffix(".docx"))
            result = pdf_to_word(args.pdf, output)
            print(f"Saved Word document: {result}")
        return 0
    except Exception as exc:
        print(f"Conversion failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
