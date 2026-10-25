import cv2
import os
import time
import threading
import requests
import playsound

# Setup YOLO model
net = cv2.dnn.readNetFromDarknet("yolov4-tiny.cfg", "yolov4-tiny.weights")
model = cv2.dnn_DetectionModel(net)
model.setInputParams(size=(416, 416), scale=1 / 255, swapRB=True)

# Load class names
classes = open("coco.names").read().strip().split("\n")

# Use absolute path for the audio file to avoid "file not found" errors
audio_path = os.path.join(os.path.dirname(__file__), "police.mp3")

# --- Phone notification settings ---
NTFY_TOPIC = "CHANGE-ME-random-topic-8472"
last_sent = 0


def notify(msg):
    global last_sent
    if time.time() - last_sent > 30:  # Rate-limit: max one notification every 30 seconds
        last_sent = time.time()
        threading.Thread(target=lambda: requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode(), timeout=5), daemon=True).start()


# --- Count people who left the frame ---
tracks, next_id, left = {}, 0, 0  # id -> [cx, cy, frames_missed]


def update(boxes, w, h, edge=50, patience=10):
    global next_id, left
    for t in tracks.values():
        t[2] += 1

    for x, y, bw, bh in boxes:
        c = (x + bw // 2, y + bh // 2)
        i = min(tracks, key=lambda k: (tracks[k][0] - c[0]) ** 2 + (tracks[k][1] - c[1]) ** 2, default=None)

        if i is None or (tracks[i][0] - c[0]) ** 2 + (tracks[i][1] - c[1]) ** 2 > 80 ** 2:
            i = next_id
            next_id += 1
        tracks[i] = [*c, 0]

    for i in [k for k, t in tracks.items() if t[2] > patience]:
        cx, cy, _ = tracks.pop(i)
        if not (edge < cx < w - edge and edge < cy < h - edge):
            left += 1


# Background audio handler
alarm_lock = threading.Lock()
is_alarm_playing = False


def play_alarm():
    global is_alarm_playing
    with alarm_lock:
        is_alarm_playing = True
    try:
        if os.path.exists(audio_path):
            playsound.playsound(audio_path)
    except Exception:
        pass
    finally:
        with alarm_lock:
            is_alarm_playing = False


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Starting WatchDog Security System... Press 'q' to quit.")

while True:
    ok, frame = cap.read()
    if not ok:
        break

    frame = cv2.flip(frame, 1)
    height, width = frame.shape[:2]

    # Run YOLO detection
    class_ids, scores, boxes = model.detect(frame, confThreshold=0.3, nmsThreshold=0.4)

    alarm_triggered = False
    person_boxes = []

    if len(boxes) > 0:
        for cid, score, box in zip(class_ids, scores, boxes):
            class_id = int(cid) if not hasattr(cid, '__len__') else int(cid[0])
            conf_score = float(score) if not hasattr(score, '__len__') else float(score[0])

            if class_id >= len(classes):
                continue

            label = classes[class_id]
            x, y, w, h = box

            if label == "person":
                person_boxes.append((x, y, w, h))

                # TRIGGER: Person detected with confidence > 0.5
                if conf_score > 0.5:
                    alarm_triggered = True
                    color = (0, 0, 255)  # Red for high-confidence person alert
                else:
                    color = (0, 255, 255)  # Yellow for low-confidence person
            else:
                color = (128, 128, 128)  # Grey for other objects

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{label} {conf_score:.2f}", (x, max(y - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    update(person_boxes, width, height)

    cv2.putText(frame, f"People Left Frame: {left}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(frame, f"Active Tracks: {len(tracks)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    if alarm_triggered:
        notify("Security Alert: Person detected with high confidence!")
        with alarm_lock:
            if not is_alarm_playing:
                threading.Thread(target=play_alarm, daemon=True).start()

    cv2.imshow("Smart WatchDog Security", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()