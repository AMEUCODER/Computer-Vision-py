# =========================================================
# MAIN — the camera loop only. No drawing logic and no face-math
# lives here; it just wires config + detection + filters together.
# =========================================================

import cv2
import config
import detection
import filters
import capture_utils


def main():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    face_mesh = detection.create_face_detector()
    capture = capture_utils.CountdownCapture()  # <-- line 1 of 2: create it once, before the loop

    current_filter = "none"
    print("1=glasses 2=crown 3=glasses+crown 4=mustache 5=clown nose "
          "6=devil horns 7=dog 0=none q=quit")

    # Maps a SINGLE filter name -> the function that works out where to draw it.
    # Every name here must have a matching builder in filters.FILTER_BUILDERS.
    # Add a new entry here (and there) when you add a new filter.
    PLACEMENT_FUNCTIONS = {
        "glasses": detection.get_glasses_placement,
        "crown": detection.get_crown_placement,
        "mustache": detection.get_mustache_placement,
        "clown_nose": detection.get_clown_nose_placement,
        "devil_horns": detection.get_devil_horns_placement,
        "dog_nose": detection.get_dog_nose_placement,
        "dog_ears": detection.get_dog_ears_placement,
    }

    # Maps a SELECTION name (what the user actually picks with a key) -> the
    # list of individual filters to draw for it. Most selections are just
    # one filter drawing itself; "all" and "dog" are combos of two filters
    # drawn one after another. This is the one place that knows about combos
    # — PLACEMENT_FUNCTIONS and FILTER_BUILDERS stay simple (one name = one
    # image = one placement, no combo logic inside them).
    FILTER_COMBOS = {
        "glasses": ["glasses"],
        "crown": ["crown"],
        "all": ["glasses", "crown"],
        "mustache": ["mustache"],
        "clown_nose": ["clown_nose"],
        "devil_horns": ["devil_horns"],
        "dog": ["dog_ears", "dog_nose"],
        "none": [],
    }

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Could not read from camera.")
            break

        frame = cv2.flip(frame, 1)  # mirror view, feels more natural
        frame_h, frame_w = frame.shape[:2]

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        points = detection.get_landmarks(face_mesh, frame_rgb, frame_w, frame_h)

        if points is not None:
            # current_filter might be "glasses" (1 item), "all"/"dog" (2 items),
            # or "none" (0 items) — FILTER_COMBOS turns it into a plain list,
            # so this loop doesn't need to know or care which case it is.
            for filter_name in FILTER_COMBOS[current_filter]:
                placement_fn = PLACEMENT_FUNCTIONS[filter_name]
                center, width, angle = placement_fn(points)

                overlay = filters.get_overlay(filter_name)
                frame = filters.overlay_image_alpha(frame, overlay, center, width, angle)

        cv2.putText(frame, f"Filter: {current_filter}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow(config.WINDOW_NAME, frame)

        # Only ONE cv2.waitKey() call per loop. Calling it twice means each
        # call steals whatever keystroke was waiting, so the two calls end up
        # fighting over the same single key press instead of sharing it.
        key = cv2.waitKey(1) & 0xFF

        # Call this UNCONDITIONALLY, every frame, not inside "if key=='c'".
        # It needs to keep running even when no key is pressed, so it can
        # keep checking "has the 5 seconds passed yet?" on its own.
        frame = capture.update(frame, key)

        if key == ord('q'):
            break
        elif key in config.FILTER_KEYS:
            current_filter = config.FILTER_KEYS[key]
            print(f"Switched to: {current_filter}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


