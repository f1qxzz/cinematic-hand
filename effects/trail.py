"""
effects/trail.py — Smooth colored trail following finger tip.
"""

from collections import deque
import numpy as np
import cv2
import config


class TrailEffect:
    def __init__(self, max_length: int = None):
        self._max  = max_length or config.TRAIL_MAX_LENGTH
        self._pts  = deque(maxlen=self._max)
        self._hue  = 0

    def update(self, x: int | None, y: int | None):
        if x is None or y is None:
            # Break the trail — push None sentinel
            if self._pts and self._pts[-1] is not None:
                self._pts.append(None)
        else:
            self._pts.append((x, y))
        self._hue = (self._hue + 2) % 180

    def draw(self, frame: np.ndarray):
        pts = list(self._pts)
        n   = len(pts)
        if n < 2:
            return

        for i in range(1, n):
            if pts[i] is None or pts[i - 1] is None:
                continue
            # Alpha fades in older segments
            alpha = (i / n) ** 1.4
            hue   = (self._hue - int((1 - alpha) * 40)) % 180
            bgr   = cv2.cvtColor(
                __import__('numpy').uint8([[[hue, 230, 255]]]),
                cv2.COLOR_HSV2BGR
            )[0][0].tolist()
            thickness = max(1, int(config.TRAIL_THICKNESS * alpha))
            # Glow pass
            glow_col = [int(c * 0.4) for c in bgr]
            cv2.line(frame, pts[i - 1], pts[i],
                     glow_col, thickness + 4, cv2.LINE_AA)
            # Core line
            cv2.line(frame, pts[i - 1], pts[i],
                     bgr, thickness, cv2.LINE_AA)

    def clear(self):
        self._pts.clear()
