"""
effects/fire.py — Fire particles bursting from all five fingertips.
"""

import math
import random
import numpy as np
import cv2
import config


class FireParticle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'decay', 'size')

    def __init__(self, x: float, y: float):
        self.x    = float(x)
        self.y    = float(y)
        self.vx   = random.uniform(-config.FIRE_SPREAD * 0.08,
                                    config.FIRE_SPREAD * 0.08)
        vy_min, vy_max = config.FIRE_RISE_SPEED
        self.vy   = random.uniform(vy_min, vy_max)   # negative = upward
        self.life  = 1.0
        self.decay = random.uniform(0.022, 0.048)
        self.size  = random.randint(4, 10)

    def update(self):
        self.x   += self.vx
        self.y   += self.vy
        self.vy  *= 0.96
        self.vx  *= 0.94
        self.life -= self.decay

    def alive(self) -> bool:
        return self.life > 0.01

    def draw(self, layer: np.ndarray):
        a  = max(0.0, self.life)
        # Fire colour: bright yellow→orange→red as life fades
        hue = int(20 * a)     # 20=yellow, 0=red in HSV
        sat = 255
        val = int(255 * a)
        bgr = cv2.cvtColor(np.uint8([[[hue, sat, val]]]),
                           cv2.COLOR_HSV2BGR)[0][0].tolist()
        sz  = max(1, int(self.size * a))
        cx, cy = int(self.x), int(self.y)
        cv2.circle(layer, (cx, cy), sz + 4, [c // 3 for c in bgr], -1)
        cv2.circle(layer, (cx, cy), sz,     bgr,                    -1)


class FireEffect:
    FINGERTIP_INDICES = [4, 8, 12, 16, 20]

    def __init__(self):
        self._particles: list[FireParticle] = []

    def update(self, pts_full: list | None):
        # Emit from all five fingertips
        if pts_full is not None:
            for i in self.FINGERTIP_INDICES:
                if i < len(pts_full):
                    x, y = pts_full[i]
                    for _ in range(config.FIRE_PARTICLE_COUNT):
                        self._particles.append(FireParticle(x, y))

    def draw(self, frame: np.ndarray):
        if not self._particles:
            return
        layer = np.zeros_like(frame)
        alive = []
        for p in self._particles:
            p.update()
            if p.alive():
                p.draw(layer)
                alive.append(p)
        self._particles = alive
        # Blend with additive compositing for fiery glow
        cv2.add(frame, layer, frame)

    def clear(self):
        self._particles.clear()
