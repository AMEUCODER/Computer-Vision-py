"""Face blurring logic (no GUI) so it can be used from the app or from scripts."""
import os

import cv2
import numpy as np

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

HERE = os.path.dirname(os.path.abspath(__file__))
YUNET_PATH = os.path.join(HERE, "face_detection_yunet_2023mar.onnx")
CASCADE_PATH = os.path.join(HERE, "haarcascade_frontalface_default.xml")

# Main detector: YuNet (built into OpenCV 4.5.4+). Far better than Haar at small,
# distant, tilted or partly turned faces, with almost no false positives.
yunet = None
if hasattr(cv2, "FaceDetectorYN") and os.path.exists(YUNET_PATH):
    # args: model, config, input size (reset per image), score threshold, NMS threshold, top_k
    yunet = cv2.FaceDetectorYN.create(YUNET_PATH, "", (320, 320), 0.6, 0.3, 5000)

# Fallback detector: Haar cascade (older, misses small/turned faces).
face_cascade = None
if hasattr(cv2, "CascadeClassifier") and os.path.exists(CASCADE_PATH):
    _c = cv2.CascadeClassifier(CASCADE_PATH)
    if not _c.empty():
        face_cascade = _c

if yunet is None and face_cascade is None:
    raise RuntimeError("No face detector available. Keep the .onnx and .xml files next to blur.py "
                       "and install OpenCV 4.x:  pip install \"opencv-python>=4.8,<5\"")

# Detection sensitivity presets = minimum confidence (0-1) a detection needs to be blurred.
# Higher = fewer false blurs (trophies, statues, reflections); lower = catches more faces.
SENSITIVITY = {"Strict": 0.90, "Balanced": 0.80, "Sensitive": 0.65}
DEFAULT_THRESHOLD = SENSITIVITY["Balanced"]
SMALL_FACE_PX = 24      # tiny/distant faces always score lower, so they get a gentler bar
SMALL_FACE_RELAX = 0.15

MAX_DETECT_SIDE = 3000  # downscale only huge photos (keeps small faces detectable, stays fast)
PAD = 0.12              # grow each face box by 12% so hairline, ears and chin are covered too


def detect_faces(frame, threshold=DEFAULT_THRESHOLD):
    """Return a list of (x, y, w, h) face boxes in full-resolution coordinates."""
    fh, fw = frame.shape[:2]
    if yunet is not None:
        scale = min(1.0, MAX_DETECT_SIDE / max(fh, fw))
        img = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else frame
        yunet.setInputSize((img.shape[1], img.shape[0]))
        low = max(0.3, threshold - SMALL_FACE_RELAX)
        yunet.setScoreThreshold(low)  # collect candidates, then apply the size-aware bar below
        _, found = yunet.detect(img)
        if found is None:
            return []
        boxes = []
        for f in found:
            x, y, w, h = (int(round(v / scale)) for v in f[:4])
            need = low if max(w, h) < SMALL_FACE_PX else threshold
            if float(f[14]) >= need:
                boxes.append((x, y, w, h))
        return boxes

    # Haar fallback - run at full resolution (shrinking the image hides distant faces)
    gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20))
    return [tuple(int(v) for v in f) for f in faces]


def blur_face(frame, ksize=51, threshold=DEFAULT_THRESHOLD):
    """Blur every detected face in `frame` (modified in place and returned).
    Returns (frame, number_of_faces)."""
    faces = detect_faces(frame, threshold)

    if ksize % 2 == 0:  # GaussianBlur kernel size must be odd
        ksize += 1

    fh, fw = frame.shape[:2]
    count = 0
    for (x, y, w, h) in faces:
        # pad the box a little, then keep it inside the image
        px, py = int(w * PAD), int(h * PAD)
        x1, y1 = max(x - px, 0), max(y - py, 0)
        x2, y2 = min(x + w + px, fw), min(y + h + py, fh)
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue

        face_roi = frame[y1:y2, x1:x2]

        # Note: ksize (the tuple) must be odd numbers. Higher numbers = blurrier.
        blurred_face = cv2.GaussianBlur(face_roi, (ksize, ksize), 0)

        frame[y1:y2, x1:x2] = blurred_face
        count += 1

    return frame, count


def read_image(path):
    """cv2.imread that also works with non-ASCII paths (Arabic names, etc.)."""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def write_image(path, img):
    ext = os.path.splitext(path)[1] or ".jpg"
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise IOError("Could not encode " + path)
    buf.tofile(path)


def unique_path(folder, filename):
    """Avoid overwriting: photo.jpg -> photo_1.jpg if it already exists."""
    base, ext = os.path.splitext(filename)
    path = os.path.join(folder, filename)
    n = 1
    while os.path.exists(path):
        path = os.path.join(folder, "%s_%d%s" % (base, n, ext))
        n += 1
    return path


def process_images(paths, output_dir, ksize=51, progress=None, threshold=DEFAULT_THRESHOLD):
    """Blur faces in each image and save to output_dir.
    progress(i, total, filename, faces_or_None, out_path, error) is called after each file.
    Returns a list of (filename, faces, error, out_path)."""
    os.makedirs(output_dir, exist_ok=True)
    results = []
    total = len(paths)
    for i, p in enumerate(paths, 1):
        name = os.path.basename(p)
        faces, err, out_path = 0, None, None
        try:
            img = read_image(p)
            if img is None:
                raise ValueError("not a readable image")
            img, faces = blur_face(img, ksize, threshold)
            out_path = unique_path(output_dir, name)
            write_image(out_path, img)
        except Exception as e:  # keep going if one file fails
            err, out_path = str(e), None
        results.append((name, faces, err, out_path))
        if progress:
            progress(i, total, name, None if err else faces, out_path, err)
    return results


def images_in_folder(folder):
    return [os.path.join(folder, f) for f in sorted(os.listdir(folder))
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS]
