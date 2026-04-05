"""
rendering/color_grading.py — Neon cinematic color grade.
  - Saturation boost
  - Contrast lift
  - Vignette
"""

import numpy as np
import cv2
import config


class ColorGradingPass:
    def __init__(self):
        self._sat  = config.COLOR_GRADE_SATURATION
        self._con  = config.COLOR_GRADE_CONTRAST
        self._vig  = config.COLOR_GRADE_VIGNETTE
        self._vignette_mask: np.ndarray | None = None

    def _build_vignette(self, H: int, W: int) -> np.ndarray:
        cx, cy = W / 2, H / 2
        Y, X = np.ogrid[:H, :W]
        # Normalised distance from centre (0 = centre, 1 = corner)
        dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
        mask = 1.0 - np.clip(dist * self._vig, 0, 1)
        return mask.astype(np.float32)

    def apply(self, frame: np.ndarray) -> np.ndarray:
        H, W = frame.shape[:2]

        # ── Saturation boost ─────────────────────────────────────────────────
        if self._sat != 1.0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[..., 1] = np.clip(hsv[..., 1] * self._sat, 0, 255)
            frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # ── Contrast (simple S-curve approximation) ───────────────────────────
        if self._con != 1.0:
            f   = frame.astype(np.float32)
            f   = (f - 128.0) * self._con + 128.0
            frame = np.clip(f, 0, 255).astype(np.uint8)

        # ── Vignette ─────────────────────────────────────────────────────────
        if self._vig > 0:
            if (self._vignette_mask is None
                    or self._vignette_mask.shape != (H, W)):
                self._vignette_mask = self._build_vignette(H, W)
            mask3 = self._vignette_mask[:, :, np.newaxis]
            frame = np.clip(frame.astype(np.float32) * mask3,
                            0, 255).astype(np.uint8)

        return frame
