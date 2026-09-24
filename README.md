# Computer Vision Playground

Real-time computer vision projects built with Python — hand gesture
recognition, live camera filters, and interactive vision tools using
OpenCV, MediaPipe, NumPy, and Tkinter. Focused on practical, real-time
image processing: tracking, filters, and gesture-controlled interfaces
balancing accuracy with performance.

## Tech Stack

| Library       | Used for                                                                              |
|-------------  |-------------------------------------------------------------------                    |
| **OpenCV**    | Camera capture, image processing, classic CV (contours, color thresholding, filters, edge detection) |
| **MediaPipe** | Pretrained ML models for hand/pose/face landmark tracking                             |
| **NumPy**     | Array/matrix math behind custom filters and geometric calculations                    |
| **Tkinter**   | Lightweight GUIs and controls where a project needs more than OpenCV's native windows |

## Projects

| Project | Description | Folder |
|---------|-------------|--------|
| **GestureLens** | Real-time webcam app using MediaPipe hand tracking to switch live filters, capture photos, and record video through hand gestures. | [`/GestureLens`](./GestureLens) |

> More projects will be added here over time - each one lives in its own
> folder with a dedicated README covering setup, controls, and how it works.

## Repository Structure

```
.
├── HandVision-filters/          # hand-gesture-controlled camera filter app
│   ├── main.py
│   ├── fingercount.py
│   ├── filters.py
│   ├── capture.py
│   ├── captures/
│   └── README.md
├── (future projects...)
└── README.md              # you are here
```

## General Setup

Each project has its own dependencies and instructions in its folder's
README, but most share this base setup:

1. Create a virtual environment:
   ```
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

2. Install common dependencies:
   ```
   pip install opencv-python mediapipe numpy
   ```
   (Tkinter ships with most standard Python installs already.)

3. Enter a project folder and run its `main.py` (or as instructed in
   that project's own README).

## Philosophy

Every project here favors:
- **Real-time performance** over maximal accuracy - detection runs on
  live video, so speed and responsiveness matter as much as precision
- **Minimal dependencies** - core CV libraries only, no heavyweight
  frameworks unless a project specifically needs one
- **Readable, commented code** - each project is meant to be learned
  from, not just run

## License

Add your preferred license here (e.g. MIT) if you plan to make this
repository public.
