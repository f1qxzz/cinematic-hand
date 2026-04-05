"""
rendering/motion_blur.py — Temporal motion blur via frame accumulation.
Blur intensity scales with pointer velocity.
"""

from collections import deque
import numpy as np
import cv2
import config


class MotionBlurPass:
    """
    Blends the current frame with a rolling buffer of previous frames.
    Alpha scales with velocity so fast movement gets more blur.
    """

    def __init__(self):
        self._buffer = deque(maxlen=config.MOTION_BLUR_FRAMES)
        self._base_alpha = config.MOTION_BLUR_ALPHA

    def apply(self, frame: np.ndarray, velocity: float = 0.0) -> np.ndarray:
        self._buffer.append(frame.copy())

        if len(self._buffer) < 2:
            return frame

        # Scale alpha with velocity (cap at 1.0)
        vel_factor = min(1.0, velocity / 30.0)
        alpha = self._base_alpha * vel_factor

        if alpha < 0.05:
            return frame   # skip blur when nearly still

        # Weighted blend: current frame dominant, older frames faded
        result = frame.astype(np.float32)
        weight = alpha
        for prev in reversed(list(self._buffer)[:-1]):
            result = cv2.addWeighted(result, 1.0 - weight,
                                     prev.astype(np.float32), weight, 0)
            weight *= 0.5   # each older frame contributes less

        return np.clip(result, 0, 255).astype(np.uint8)

    def reset(self):
        self._buffer.clear()
