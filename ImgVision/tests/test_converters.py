from pathlib import Path
import pytest

from converters.main import build_parser, images_to_pdf, pdf_to_images, pdf_to_word


def test_converter_parser_accepts_all_three_commands():
    parser = build_parser()
    assert parser.parse_args(["img2pdf", "a.jpg", "-o", "x.pdf"]).command == "img2pdf"
    assert parser.parse_args(["pdf2img", "a.pdf"]).command == "pdf2img"
    assert parser.parse_args(["pdf2word", "a.pdf"]).command == "pdf2word"


def test_img2pdf_rejects_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        images_to_pdf([str(tmp_path / "missing.png")], str(tmp_path / "out.pdf"))


def test_pdf_converters_reject_missing_input(tmp_path):
    with pytest.raises(FileNotFoundError):
        pdf_to_images(str(tmp_path / "missing.pdf"), str(tmp_path / "pages"))
    with pytest.raises(FileNotFoundError):
        pdf_to_word(str(tmp_path / "missing.pdf"), str(tmp_path / "out.docx"))
