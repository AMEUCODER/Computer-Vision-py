# Repair notes

## Repaired build

- Restored the missing `engine/` package: tool base class, parameter schema, shared CLI runner, batch input handling, output writing, and a basic Tkinter tool window.
- Restored the missing `crop/` and `rotate_flip/` tools so the root launcher and README examples resolve correctly.
- Updated Adjust and Auto Enhance to preserve alpha transparency, including palette images with transparency metadata.
- Made Blur's background mode work without the removed MediaPipe dependency by using an OpenCV GrabCut foreground estimate with a soft fallback mask.
- Split FaceBlur's command-line entry point from its CustomTkinter interface so CLI processing does not require CustomTkinter.
- Added a FaceBlur adapter for the main ImgVision tool picker.
- Added Outpainting CLI support for custom dimensions, presets, anchors, folder processing, and output naming; fixed imports for both direct-script and package execution.
- Rebuilt the previously empty WaterMark scripts with text overlay, transparent-logo overlay, and selected-region OpenCV inpainting commands.
- Added dependency files, usage documentation, ignore rules, and regression tests.

## Verification

- Python syntax compilation passed.
- All six tool modules' CLI help commands passed.
- CLI smoke tests passed for each core tool, FaceBlur, Outpainting, and all three WaterMark operations, including an Arabic/non-ASCII filename.
- Regression tests: `7 passed`.

The GUI code compiles, but desktop window interaction was not exercised in this headless environment. FaceBlur's separate desktop window additionally requires the optional `customtkinter` dependency from `requirements-gui.txt`.
