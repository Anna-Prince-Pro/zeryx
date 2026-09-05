"""Run the STARK//CODE Doctor Strange-style webcam spell prototype."""

from pathlib import Path
import time

import cv2

from hand_tracker import HandTracker
from spell_effect import SpellEffect


WINDOW_TITLE = "STARK//CODE  |  Cast a circle spell  |  Q to quit"


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    model_path = project_dir / "models" / "hand_landmarker.task"
    tracker = HandTracker(model_path)
    spell = SpellEffect()
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        tracker.close()
        raise RuntimeError("Could not open the webcam. Check that it is not in use.")

    print("STARK//CODE ready. Draw a large circle with your index finger. Press Q to quit.")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Could not read a webcam frame.")
                break

            # Mirroring makes the spell follow the user's on-screen hand naturally.
            frame = cv2.flip(frame, 1)
            now = time.monotonic()
            index_tip = tracker.index_tip(frame)
            spell.add_tip(index_tip, now)
            spell.update_and_draw(frame, now)

            if index_tip:
                x, y = index_tip
                cv2.circle(frame, index_tip, 9, (0, 230, 255), 2, cv2.LINE_AA)
                cv2.putText(frame, f"INDEX  X:{x}  Y:{y}", (22, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (120, 230, 255), 2, cv2.LINE_AA)
            elif not spell.last_geometry:
                cv2.putText(frame, "Raise your index finger to begin casting", (22, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (120, 230, 255), 2, cv2.LINE_AA)

            cv2.imshow(WINDOW_TITLE, frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                break
    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
