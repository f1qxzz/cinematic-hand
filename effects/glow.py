"""
effects/glow.py — Glow halo + pulsing aura around a point.
"""

import math
import time
import numpy as np
import cv2
import config


def draw_glow(frame: np.ndarray, x: int, y: int,
              color: tuple, radius: int = 18):
    """
    Soft glow circle — blurred overlay blended into frame.
    """
    overlay = np.zeros_like(frame)
    cv2.circle(overlay, (x, y), radius + 14, [c // 3 for c in color], -1)
    cv2.circle(overlay, (x, y), radius,      color,                    -1)
    blur = cv2.GaussianBlur(overlay, (config.GLOW_BLUR_KSIZE,
                                      config.GLOW_BLUR_KSIZE), 0)
    cv2.addWeighted(blur, config.GLOW_INTENSITY, frame, 1.0, 0, frame)


class AuraEffect:
    """
    Pulsing concentric aura rings around a point.
    Colors cycle through a given HSV hue list.
    """

    def __init__(self, hue_list: list[tuple] | None = None):
        self._hues = hue_list or [(160, 230, 255), (140, 210, 255), (120, 200, 255)]
        self._phase = 0.0

    def draw(self, frame: np.ndarray, x: int, y: int,
             radius: int = None, speed: float = None):
        radius = radius or config.AURA_RADIUS
        speed  = speed  or config.AURA_PULSE_SPEED
        t      = time.time() * speed + self._phase

        overlay = np.zeros_like(frame)
        for i, hsv in enumerate(self._hues):
            r     = radius + int(12 * math.sin(t + i * 1.0))
            alpha = 0.6 - i * 0.15
            bgr   = cv2.cvtColor(
                np.uint8([[list(hsv)]]), cv2.COLOR_HSV2BGR
            )[0][0].tolist()
            cv2.circle(overlay, (x, y), r, bgr, 3, cv2.LINE_AA)

        blur = cv2.GaussianBlur(overlay, (21, 21), 0)
        cv2.addWeighted(blur, 0.55, frame, 1.0, 0, frame)
        cv2.addWeighted(overlay, 0.3, frame, 1.0, 0, frame)

    def set_phase(self, phase: float):
        self._phase = phase
