"""
effects/particle.py — Generic particle system (smooth, HSV-colored).
"""

import math
import random
import numpy as np
import cv2
import config


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'decay', 'size', 'color', 'gravity')

    def __init__(self, x: float, y: float, color: tuple):
        self.x = float(x)
        self.y = float(y)
        angle  = random.uniform(0, 2 * math.pi)
        speed  = random.uniform(2, 9)
        self.vx      = math.cos(angle) * speed
        self.vy      = math.sin(angle) * speed - random.uniform(1, 4)
        self.life    = 1.0
        self.decay   = random.uniform(0.018, 0.038)
        self.size    = random.randint(3, 9)
        self.color   = color
        self.gravity = config.PARTICLE_GRAVITY

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += self.gravity
        self.vx *= 0.97
        self.life -= self.decay

    def alive(self) -> bool:
        return self.life > 0.01


class ParticleSystem:
    def __init__(self):
        self._particles: list[Particle] = []

    def emit(self, x: float, y: float, count: int = None, hue_range: tuple = (0, 179)):
        count = count or config.PARTICLE_COUNT_PER_FRAME
        for _ in range(count):
            hue = random.randint(*hue_range)
            bgr = cv2.cvtColor(
                np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR
            )[0][0].tolist()
            if len(self._particles) < config.PARTICLE_MAX:
                self._particles.append(Particle(x, y, bgr))

    def update_and_draw(self, frame: np.ndarray):
        if not self._particles:
            return
        layer = np.zeros_like(frame)
        alive = []
        for p in self._particles:
            p.update()
            if p.alive():
                a  = max(0.0, p.life)
                col = [int(c * a) for c in p.color]
                sz  = max(1, int(p.size * a))
                cx, cy = int(p.x), int(p.y)
                cv2.circle(layer, (cx, cy), sz + 3, [c // 2 for c in col], -1)
                cv2.circle(layer, (cx, cy), sz,     col,                    -1)
                alive.append(p)
        self._particles = alive
        cv2.add(frame, layer, frame)

    def clear(self):
        self._particles.clear()

    def count(self) -> int:
        return len(self._particles)
