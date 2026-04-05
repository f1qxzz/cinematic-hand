"""
core/motion.py — Motion & velocity analysis.
Feeds lightning threshold, motion blur intensity, etc.
"""

import math
from collections import deque


class MotionTracker:
    """
    Tracks pointer motion over time.
    Provides smoothed speed, direction, and acceleration.
    """

    def __init__(self, window: int = 5):
        self._positions  = deque(maxlen=window + 1)
        self._velocities = deque(maxlen=window)
        self._speed_ema  = 0.0
        self._alpha      = 0.4

    def update(self, x: int | None, y: int | None):
        if x is None or y is None:
            return
        self._positions.append((x, y))
        if len(self._positions) >= 2:
            p1 = self._positions[-2]
            p2 = self._positions[-1]
            vx = p2[0] - p1[0]
            vy = p2[1] - p1[1]
            speed = math.hypot(vx, vy)
            self._velocities.append((vx, vy, speed))
            self._speed_ema = (self._alpha * speed
                               + (1 - self._alpha) * self._speed_ema)

    def speed(self) -> float:
        """EMA-smoothed speed in px/frame."""
        return self._speed_ema

    def velocity_vec(self) -> tuple[float, float]:
        if not self._velocities:
            return 0.0, 0.0
        vx_avg = sum(v[0] for v in self._velocities) / len(self._velocities)
        vy_avg = sum(v[1] for v in self._velocities) / len(self._velocities)
        return vx_avg, vy_avg

    def direction_deg(self) -> float:
        """Direction of motion in degrees (0 = right, 90 = down)."""
        vx, vy = self.velocity_vec()
        return math.degrees(math.atan2(vy, vx))

    def reset(self):
        self._positions.clear()
        self._velocities.clear()
        self._speed_ema = 0.0
