# WaterMark tools

Command-line tools for adding a text watermark, overlaying a transparent logo, or inpainting a selected rectangular area.

```bash
python WaterMark/main.py text photo.jpg --text "© My Brand" --position bottom-right
python WaterMark/main.py text photo.jpg --text "علامتي" --font path/to/arabic-font.ttf --color "#fff"
python WaterMark/main.py logo photo.jpg --logo logo.png --scale 0.16 --opacity 180
python WaterMark/main.py remove photo.jpg --box 20 30 220 100 --method telea
```

The default output is written next to the input with `_watermarked`, `_logo`, or `_cleaned` appended to the filename. Use `-o` to choose another output path.

The removal command uses OpenCV inpainting and is intended for a manually selected rectangle. It works best on simple surrounding areas; it cannot reliably recover detailed objects or textures fully covered by the watermark.
