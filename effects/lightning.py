"""
effects/lightning.py — Recursive lightning bolt, triggered by fast gesture.
"""

import math
import random
import numpy as np
import cv2
import config


def _bolt(pts: list, p1: tuple, p2: tuple, deviation: float, depth: int):
    """Recursive midpoint displacement for jagged lightning."""
    if depth == 0 or deviation < 1:
        pts.append(p1)
        pts.append(p2)
        return
    mx = (p1[0] + p2[0]) / 2 + random.uniform(-deviation, deviation)
    my = (p1[1] + p2[1]) / 2 + random.uniform(-deviation, deviation)
    mid = (int(mx), int(my))
    _bolt(pts, p1,  mid, deviation * 0.55, depth - 1)
    _bolt(pts, mid, p2,  deviation * 0.55, depth - 1)


class LightningEffect:
    def __init__(self):
        self._bolts: list[list[tuple]] = []
        self._life:  list[float]       = []

    def trigger(self, x1: int, y1: int, x2: int, y2: int):
        """Spawn a new lightning bolt between two points."""
        pts: list[tuple] = []
        _bolt(pts, (x1, y1), (x2, y2),
              config.LIGHTNING_DEVIATION, config.LIGHTNING_SEGMENTS)
        self._bolts.append(pts)
        self._life.append(1.0)

    def update_and_draw(self, frame: np.ndarray):
        if not self._bolts:
            return
        layer = np.zeros_like(frame)
        alive_bolts = []
        alive_life  = []

        for pts, life in zip(self._bolts, self._life):
            if life <= 0:
                continue
            alpha = max(0.0, life)
            # Glow pass
            for i in range(0, len(pts) - 1, 2):
                glow_col = (int(50 * alpha), int(50 * alpha), int(255 * alpha))
                cv2.line(layer, pts[i], pts[i + 1], glow_col, 5, cv2.LINE_AA)
            # Core white-blue
            for i in range(0, len(pts) - 1, 2):
                core_col = (int(200 * alpha), int(200 * alpha), 255)
                cv2.line(layer, pts[i], pts[i + 1], core_col, 2, cv2.LINE_AA)

            new_life = life - 0.12   # fade out
            if new_life > 0:
                alive_bolts.append(pts)
                alive_life.append(new_life)

        self._bolts = alive_bolts
        self._life  = alive_life

        blur = cv2.GaussianBlur(layer, (7, 7), 0)
        cv2.add(frame, blur,  frame)
        cv2.add(frame, layer, frame)

    def clear(self):
        self._bolts.clear()
        self._life.clear()
