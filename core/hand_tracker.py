"""
core/hand_tracker.py — MediaPipe hand landmark detection.
Handles model download, camera threading, and landmark extraction.
"""

import os
import threading
import urllib.request
import time

import cv2
import numpy as np

try:
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python.vision import (
        HandLandmarker, HandLandmarkerOptions, RunningMode,
    )
    from mediapipe import Image, ImageFormat
except ImportError:
    raise ImportError("Install mediapipe: pip install mediapipe>=0.10.0")

import config

# ── Landmark index constants (re-exported for other modules) ─────────────────
WRIST       = 0
THUMB_TIP   = 4;  THUMB_IP   = 3;  THUMB_MCP  = 2
INDEX_TIP   = 8;  INDEX_PIP  = 6;  INDEX_MCP  = 5
MIDDLE_TIP  = 12; MIDDLE_PIP = 10; MIDDLE_MCP = 9
RING_TIP    = 16; RING_PIP   = 14; RING_MCP   = 13
PINKY_TIP   = 20; PINKY_PIP  = 18; PINKY_MCP  = 17

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]
FINGERTIP_INDICES = {4, 8, 12, 16, 20}


# ── Model downloader ─────────────────────────────────────────────────────────
def ensure_model() -> None:
    if os.path.exists(config.MODEL_PATH):
        return
    print(f"[HandTracker] Downloading MediaPipe model (~8 MB) ...")
    try:
        urllib.request.urlretrieve(config.MODEL_URL, config.MODEL_PATH)
        print("[HandTracker] Model ready.")
    except Exception as exc:
        print(f"[HandTracker] Download failed: {exc}")
        print(f"  Manual download: {config.MODEL_URL}")
        print(f"  Save as: {config.MODEL_PATH}")
        raise


# ── Threaded camera reader ────────────────────────────────────────────────────
class CameraReader:
    """Reads frames in a background thread to eliminate buffering lag."""

    def __init__(self, src: int = 0, w: int = 1280, h: int = 720):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.cap.set(cv2.CAP_PROP_FPS,          config.TARGET_FPS)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)

        self._frame = None
        self._lock  = threading.Lock()
        self._stop  = False
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self):
        while not self._stop:
            ok, frame = self.cap.read()
            if ok:
                with self._lock:
                    self._frame = frame

    def read(self):
        with self._lock:
            if self._frame is None:
                return False, None
            return True, self._frame.copy()

    def size(self):
        return (
            int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )

    def release(self):
        self._stop = True
        self._thread.join(timeout=1)
        self.cap.release()


# ── Hand tracker ─────────────────────────────────────────────────────────────
class HandTracker:
    """
    Wraps MediaPipe HandLandmarker.
    Detects on a downscaled frame, returns scaled-up landmarks.
    """

    def __init__(self):
        ensure_model()
        options = HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(
                model_asset_path=config.MODEL_PATH,
            ),
            running_mode=RunningMode.IMAGE,
            num_hands=config.NUM_HANDS,
            min_hand_detection_confidence=config.MIN_DETECTION_CONF,
            min_hand_presence_confidence=config.MIN_PRESENCE_CONF,
            min_tracking_confidence=config.MIN_TRACKING_CONF,
        )
        self._detector = HandLandmarker.create_from_options(options)

    def detect(self, frame_bgr: np.ndarray):
        """
        Args:
            frame_bgr: full-resolution BGR frame (already flipped)

        Returns:
            dict with:
                'detected'   : bool
                'landmarks'  : list of 21 landmark objects (normalised [0,1])
                'hand_label' : 'Left' | 'Right' | None
                'pts_full'   : list of (x, y) in full-res pixel coords
        """
        H, W = frame_bgr.shape[:2]
        dw, dh = config.DETECT_WIDTH, config.DETECT_HEIGHT
        small = cv2.resize(frame_bgr, (dw, dh))
        rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        mp_img = Image(image_format=ImageFormat.SRGB, data=rgb)
        result = self._detector.detect(mp_img)

        if not result.hand_landmarks or not result.handedness:
            return {
                'detected':   False,
                'landmarks':  None,
                'hand_label': None,
                'pts_full':   None,
            }

        lms   = result.hand_landmarks[0]
        label = result.handedness[0][0].category_name
        pts   = [(int(lm.x * W), int(lm.y * H)) for lm in lms]

        return {
            'detected':   True,
            'landmarks':  lms,
            'hand_label': label,
            'pts_full':   pts,
        }

    def close(self):
        self._detector.close()
