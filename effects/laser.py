"""
effects/laser.py — Neon laser beam emitted from index fingertip.
Extends in the direction the finger is pointing.
"""

import math
import numpy as np
import cv2
import config


class LaserEffect:
    def __init__(self):
        self._hue = 90   # start cyan

    def draw(self, frame: np.ndarray, pts_full: list,
             index_tip_idx: int = 8, index_pip_idx: int = 6):
        """
        Draws a laser from the tip through the knuckle, extending outward.
        pts_full: list of (x, y) in full-res coords.
        """
        if pts_full is None or len(pts_full) < 21:
            return

        tx, ty = pts_full[index_tip_idx]
        px, py = pts_full[index_pip_idx]

        # Direction from PIP → TIP, then extend
        dx = tx - px
        dy = ty - py
        length = math.hypot(dx, dy)
        if length < 1:
            return

        nx = dx / length
        ny = dy / length
        ex = int(tx + nx * config.LASER_LENGTH)
        ey = int(ty + ny * config.LASER_LENGTH)

        self._hue = (self._hue + 3) % 180
        bgr = cv2.cvtColor(
            np.uint8([[[self._hue, 255, 255]]]), cv2.COLOR_HSV2BGR
        )[0][0].tolist()
        white = (255, 255, 255)

        # Outer glow
        glow_col = [c // 3 for c in bgr]
        cv2.line(frame, (tx, ty), (ex, ey), glow_col,
                 config.LASER_THICKNESS + 6, cv2.LINE_AA)
        # Mid glow
        cv2.line(frame, (tx, ty), (ex, ey), bgr,
                 config.LASER_THICKNESS + 2, cv2.LINE_AA)
        # Core white
        cv2.line(frame, (tx, ty), (ex, ey), white,
                 max(1, config.LASER_THICKNESS - 1), cv2.LINE_AA)

        # Tip flare
        cv2.circle(frame, (tx, ty), 7, white, -1)
        cv2.circle(frame, (tx, ty), 12, bgr, 2, cv2.LINE_AA)
