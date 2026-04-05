"""
rendering/bloom.py — Bloom post-process: brighten hot pixels, blur, blend.
"""

import numpy as np
import cv2
import config


class BloomPass:
    """
    Extracts pixels above a brightness threshold,
    applies Gaussian blur, then additively blends back.
    """

    def __init__(self):
        self._ksize = config.BLOOM_BLUR_KSIZE
        self._thresh = config.BLOOM_THRESHOLD
        self._intensity = config.BLOOM_INTENSITY

    def apply(self, frame: np.ndarray) -> np.ndarray:
        # Convert to HSV to isolate bright pixels
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        _, _, v = cv2.split(hsv)

        # Mask of bright regions
        _, mask = cv2.threshold(v, self._thresh, 255, cv2.THRESH_BINARY)
        bright = cv2.bitwise_and(frame, frame, mask=mask)

        # Blur the bright layer
        k = self._ksize if self._ksize % 2 == 1 else self._ksize + 1
        blurred = cv2.GaussianBlur(bright, (k, k), 0)

        # Additive blend
        out = cv2.addWeighted(frame, 1.0, blurred, self._intensity, 0)
        return out
