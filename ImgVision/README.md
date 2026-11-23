# ImgVision

ImgVision is a collection of image-processing tools and document converters. The image tools share a small runtime and can also be run independently.

## Setup

Use Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
```

Optional dependencies:

```bash
python -m pip install -r requirements-converters.txt  # img2pdf, PDF rendering, PDF-to-Word
python -m pip install -r requirements-gui.txt          # CustomTkinter GUI extras
```

`tkinter` is used by the desktop windows and may need to be installed separately on some Linux distributions.

## Launch and discover tools

```bash
python run_tool.py
python run_tool.py list
python run_tool.py adjust photo.jpg --brightness 1.2 --warmth 10 -o edited.jpg
```

## Image tools

| Tool | Example |
|---|---|
| Adjust | `python -m adjust photo.jpg --brightness 1.2 --warmth 10 -o edited.jpg` |
| Auto Enhance | `python -m auto_enhance photo.jpg -o enhanced.jpg` |
| Blur | `python -m blur photo.jpg --mode background --strength 15` |
| Crop | `python -m crop photo.jpg --aspect 9:16 --zoom 1.5 -o cropped.jpg` |
| Face Blur | `python -m face_blur photos/ -o blurred/ --strength 71 --sensitivity Sensitive` |
| Rotate & Flip | `python -m rotate_flip photo.jpg --turn 90 --flip-h` |
| Background Outpainting | `python outpainting/main.py photo.jpg --size 1080x1920 --anchor bottom` |
| Watermark | `python WaterMark/main.py text photo.jpg --text "© My Brand"` |

Most image tools accept either one image or a folder. Use `-o` to select an output path/folder and `--recursive` to include nested folders where supported.

## Document converters

Install `requirements-converters.txt` before using these commands.

### 1. Images to PDF (img2pdf)

Combine multiple images into one PDF. The image order is the PDF page order.

```bash
python run_tool.py convert img2pdf page1.jpg page2.png -o document.pdf
```

### 2. PDF to images

Each PDF page becomes a separate image. PyMuPDF is used, so Poppler is not required.

```bash
python run_tool.py convert pdf2img document.pdf -o pages/ --dpi 200 --format png
```

Supported output formats: `png`, `jpg`, `jpeg`. Higher DPI creates sharper but larger images.

### 3. PDF to Word

Convert a PDF into an editable `.docx` file:

```bash
python run_tool.py convert pdf2word document.pdf -o document.docx
```

PDF-to-Word conversion may not preserve complex layouts, tables, fonts, or scanned text perfectly. Scanned PDFs may need OCR before their text is editable.

### Optional: Word to PDF

```bash
python run_tool.py word2pdf document.docx -o document.pdf
```

`docx2pdf` generally requires Microsoft Word and is intended for Windows/macOS.

## Watermark notes

Watermark removal uses OpenCV inpainting inside a manually selected rectangle. Results vary; it works best on simple surrounding backgrounds and cannot reliably reconstruct complex details hidden underneath.

## Notes

- Image loading applies EXIF orientation.
- Core image formats include JPEG, PNG, WebP, BMP, and TIFF.
- The core image tools do not require a GPU or cloud service.
