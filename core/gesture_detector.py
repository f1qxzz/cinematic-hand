"""
core/gesture_detector.py — Stable gesture classification.

Uses:
  - 10-frame buffer + majority voting
  - confidence score (vote ratio)
  - 0.3s cooldown between mode switches
  - Explicit ILY: thumb + index + pinky up, middle + ring down
"""

import time
from collections import deque
import config

# Landmark indices imported from hand_tracker to avoid circular deps
WRIST       = 0
THUMB_TIP   = 4;  THUMB_IP   = 3
INDEX_TIP   = 8;  INDEX_PIP  = 6
MIDDLE_TIP  = 12; MIDDLE_PIP = 10
RING_TIP    = 16; RING_PIP   = 14
PINKY_TIP   = 20; PINKY_PIP  = 18


def finger_states(landmarks, hand_label: str) -> list[int]:
    """
    Returns [thumb, index, middle, ring, pinky] — 1 = extended, 0 = curled.
    Mirrors thumb direction based on which hand it is.
    """
    lx = lambda i: landmarks[i].x
    ly = lambda i: landmarks[i].y

    # Thumb (horizontal comparison)
    if hand_label == "Right":
        thumb_up = 1 if lx(THUMB_TIP) < lx(THUMB_IP) else 0
    else:
        thumb_up = 1 if lx(THUMB_TIP) > lx(THUMB_IP) else 0

    # Four fingers (vertical comparison — lower y = higher on screen)
    fingers = [thumb_up]
    for tip, pip in [
        (INDEX_TIP,  INDEX_PIP),
        (MIDDLE_TIP, MIDDLE_PIP),
        (RING_TIP,   RING_PIP),
        (PINKY_TIP,  PINKY_PIP),
    ]:
        fingers.append(1 if ly(tip) < ly(pip) else 0)

    return fingers  # [thumb, index, middle, ring, pinky]


def classify_raw(up: list[int]) -> str:
    """
    Pure function — maps finger state vector to gesture string.
    Called per-frame before buffering.
    """
    thumb, idx, mid, ring, pinky = up
    total = sum(up)

    # ILY 🤟 — thumb + index + pinky, NOT middle/ring
    if thumb == 1 and idx == 1 and mid == 0 and ring == 0 and pinky == 1:
        return "ILY"

    # Open hand ✋
    if total == 5:
        return "OPEN_HAND"

    # Pointing ☝ — only index up
    if idx == 1 and total == 1:
        return "POINTING"

    # Peace ✌ — index + middle
    if idx == 1 and mid == 1 and total == 2:
        return "PEACE"

    # Thumbs up 👍 — only thumb
    if thumb == 1 and total == 1:
        return "THUMBS_UP"

    # Fist ✊ — nothing up
    if total == 0:
        return "FIST"

    return "OTHER"


class GestureDetector:
    """
    Stateful wrapper that adds:
      - Circular buffer (GESTURE_BUFFER_SIZE frames)
      - Majority voting + confidence score
      - Cooldown timer
    """

    def __init__(self):
        self._buffer = deque(maxlen=config.GESTURE_BUFFER_SIZE)
        self._last_switch: float = 0.0
        self._stable_gesture: str = "OTHER"
        self._confidence: float   = 0.0

    # ── Public ────────────────────────────────────────────────────────────────

    def update(self, landmarks, hand_label: str) -> tuple[str, float]:
        """
        Args:
            landmarks: list of 21 landmark objects from MediaPipe
            hand_label: 'Left' | 'Right'

        Returns:
            (stable_gesture, confidence)
        """
        up      = finger_states(landmarks, hand_label)
        raw     = classify_raw(up)
        self._buffer.append(raw)

        # Majority vote
        counts = {}
        for g in self._buffer:
            counts[g] = counts.get(g, 0) + 1
        winner     = max(counts, key=counts.__getitem__)
        confidence = counts[winner] / len(self._buffer)

        self._confidence = confidence
        if (
            confidence >= config.GESTURE_CONFIDENCE_MIN
            and winner != self._stable_gesture
            and (time.time() - self._last_switch) >= config.GESTURE_COOLDOWN_SEC
        ):
            self._stable_gesture = winner
            self._last_switch    = time.time()

        return self._stable_gesture, self._confidence

    def reset(self):
        self._buffer.clear()
        self._stable_gesture = "OTHER"
        self._confidence     = 0.0

    @property
    def gesture(self) -> str:
        return self._stable_gesture

    @property
    def confidence(self) -> float:
        return self._confidence
