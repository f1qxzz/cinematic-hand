"""
core/gesture_smoother.py — EMA smoothing + velocity tracking for pointer.
"""

import math
from collections import deque
import config


class GestureSmoother:
    """
    Exponential Moving Average (EMA) smoother for hand landmark positions.

    smoothed = alpha * current + (1 - alpha) * prev

    Also tracks velocity and provides interpolation between frames.
    """

    def __init__(self, alpha: float = None):
        self._alpha    = alpha or config.EMA_ALPHA
        self._v_alpha  = config.VELOCITY_ALPHA

        self._sx: float | None = None   # smoothed x
        self._sy: float | None = None   # smoothed y
        self._vx: float = 0.0           # velocity x (EMA)
        self._vy: float = 0.0           # velocity y (EMA)

        # Rolling average window for extra stability
        self._history = deque(maxlen=config.POINTER_HISTORY)

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, x: float, y: float):
        """Feed a new raw observation."""
        if self._sx is None:
            # First frame — initialise
            self._sx, self._sy = float(x), float(y)
            self._vx, self._vy = 0.0, 0.0
        else:
            # Raw velocity
            raw_vx = x - self._sx
            raw_vy = y - self._sy

            # EMA on velocity
            self._vx = self._v_alpha * raw_vx + (1 - self._v_alpha) * self._vx
            self._vy = self._v_alpha * raw_vy + (1 - self._v_alpha) * self._vy

            # EMA on position
            self._sx = self._alpha * x + (1 - self._alpha) * self._sx
            self._sy = self._alpha * y + (1 - self._alpha) * self._sy

        self._history.append((self._sx, self._sy))

    def get(self) -> tuple[int | None, int | None]:
        """Return rolling-average smoothed (x, y) as integers."""
        if not self._history:
            return None, None
        avg_x = sum(p[0] for p in self._history) / len(self._history)
        avg_y = sum(p[1] for p in self._history) / len(self._history)
        return int(avg_x), int(avg_y)

    def velocity(self) -> float:
        """Return current speed magnitude in px/frame."""
        return math.hypot(self._vx, self._vy)

    def velocity_vec(self) -> tuple[float, float]:
        return self._vx, self._vy

    def interpolate(self, steps: int = None) -> list[tuple[int, int]]:
        """
        Return sub-frame interpolated positions between previous
        and current smoothed position.  Useful for trail rendering.
        """
        steps = steps or config.INTERP_STEPS
        if len(self._history) < 2:
            sx, sy = self.get()
            return [(sx, sy)] if sx is not None else []
        prev_x, prev_y = self._history[-2]
        curr_x, curr_y = self._history[-1]
        pts = []
        for i in range(1, steps + 1):
            t = i / steps
            pts.append((
                int(prev_x + (curr_x - prev_x) * t),
                int(prev_y + (curr_y - prev_y) * t),
            ))
        return pts

    def reset(self):
        self._sx = self._sy = None
        self._vx = self._vy = 0.0
        self._history.clear()
