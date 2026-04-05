"""
effects/ily.py — Full "I Love You 🤟" cinematic mode.

Features:
  - Dark background (ILY_BG_DARKEN)
  - Subtle zoom (ILY_ZOOM_FACTOR)
  - Neon cycling aura: pink → purple → blue
  - Heart particles floating up
  - Energy burst on first activation
  - Pulsing "I LOVE YOU ❤" text
  - Slow-motion simulation (caller adjusts emit rate)
"""

import math
import random
import time
import numpy as np
import cv2
import config


# ── Heart particle ────────────────────────────────────────────────────────────
class HeartParticle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'decay', 'scale', 'hue')

    def __init__(self, x: float, y: float):
        self.x     = float(x)
        self.y     = float(y)
        self.vx    = random.uniform(-1.8, 1.8)
        self.vy    = random.uniform(-4, -1.5)
        self.life  = 1.0
        self.decay = random.uniform(0.010, 0.022)
        self.scale = random.uniform(0.5, 1.6)
        self.hue   = random.randint(145, 170)   # pink-purple range

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.03   # very light gravity
        self.life -= self.decay

    def alive(self) -> bool:
        return self.life > 0.01

    def draw(self, layer: np.ndarray):
        a   = max(0.0, self.life)
        hue = (self.hue + int((1 - a) * 20)) % 180
        bgr = cv2.cvtColor(np.uint8([[[hue, 220, 255]]]),
                           cv2.COLOR_HSV2BGR)[0][0].tolist()
        s   = max(1, int(12 * self.scale * a))
        cx, cy = int(self.x), int(self.y)
        # Two circles + filled triangle = heart
        cv2.circle(layer, (cx - s // 2, cy - s // 4), s // 2, bgr, -1)
        cv2.circle(layer, (cx + s // 2, cy - s // 4), s // 2, bgr, -1)
        pts = np.array([[cx - s, cy],
                        [cx + s, cy],
                        [cx,     cy + s + s // 2]])
        cv2.fillPoly(layer, [pts], bgr)


# ── ILY text effect ───────────────────────────────────────────────────────────
class ILYTextEffect:
    def __init__(self, W: int, H: int):
        self.W = W
        self.H = H
        self._timer = 0.0
        self._hue   = 160

    def update(self):
        self._timer += 0.04
        self._hue = (self._hue + 1) % 180

    def draw(self, frame: np.ndarray):
        scale  = 1.0 + 0.14 * math.sin(self._timer * 3.2)
        fs     = 1.9 * scale
        thick  = max(2, int(4 * scale))
        text   = "I  LOVE  YOU  <3"
        bgr    = cv2.cvtColor(np.uint8([[[self._hue, 220, 255]]]),
                              cv2.COLOR_HSV2BGR)[0][0].tolist()
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, fs, thick)
        tx = self.W // 2 - tw // 2
        ty = int(self.H * 0.40 + math.sin(self._timer * 2.1) * 20)
        # Drop shadow
        cv2.putText(frame, text, (tx + 3, ty + 3),
                    cv2.FONT_HERSHEY_DUPLEX, fs, (10, 10, 10),
                    thick + 3, cv2.LINE_AA)
        # Glow
        cv2.putText(frame, text, (tx, ty),
                    cv2.FONT_HERSHEY_DUPLEX, fs, [c // 2 for c in bgr],
                    thick + 6, cv2.LINE_AA)
        # Main
        cv2.putText(frame, text, (tx, ty),
                    cv2.FONT_HERSHEY_DUPLEX, fs, bgr, thick, cv2.LINE_AA)


# ── Full ILY mode manager ─────────────────────────────────────────────────────
class ILYEffect:
    def __init__(self, W: int, H: int):
        self.W = W
        self.H = H
        self._text   = ILYTextEffect(W, H)
        self._hearts: list[HeartParticle] = []
        self._aura_hue  = 160
        self._aura_phase = 0.0
        self._active     = False
        self._burst_done = False

    def activate(self):
        if not self._active:
            self._active     = True
            self._burst_done = False

    def deactivate(self):
        self._active = False
        self._hearts.clear()

    @property
    def active(self) -> bool:
        return self._active

    def emit_hearts(self, x: float, y: float, count: int = None):
        count = count or config.ILY_HEART_PER_FRAME
        for _ in range(count):
            self._hearts.append(HeartParticle(x, y))

    def energy_burst(self, x: float, y: float):
        """One-shot burst of many hearts."""
        for _ in range(config.ILY_BURST_PARTICLES):
            hp = HeartParticle(x, y)
            hp.vx *= 3.5
            hp.vy = random.uniform(-10, -2)
            hp.decay *= 0.6
            self._hearts.append(hp)
        self._burst_done = True

    def draw(self, frame: np.ndarray, x: int | None, y: int | None):
        if not self._active:
            return

        H, W = frame.shape[:2]

        # 1. Darken background
        frame[:] = (frame * config.ILY_BG_DARKEN).astype(np.uint8)

        # 2. Subtle zoom
        zf = config.ILY_ZOOM_FACTOR
        if zf > 1.0:
            new_h, new_w = int(H * zf), int(W * zf)
            zoomed = cv2.resize(frame, (new_w, new_h))
            oy = (new_h - H) // 2
            ox = (new_w - W) // 2
            frame[:] = zoomed[oy:oy + H, ox:ox + W]

        # 3. Neon aura rings
        if x is not None and y is not None:
            self._aura_phase += 0.06
            overlay = np.zeros_like(frame)
            for i, hsv in enumerate(config.ILY_AURA_COLORS):
                r   = config.AURA_RADIUS + int(16 * math.sin(self._aura_phase + i * 1.1))
                bgr = cv2.cvtColor(np.uint8([[list(hsv)]]),
                                   cv2.COLOR_HSV2BGR)[0][0].tolist()
                cv2.circle(overlay, (x, y), r,      bgr, 3, cv2.LINE_AA)
                cv2.circle(overlay, (x, y), r + 6, [c // 3 for c in bgr], 6, cv2.LINE_AA)
            blur = cv2.GaussianBlur(overlay, (27, 27), 0)
            cv2.addWeighted(blur,    0.65, frame, 1.0, 0, frame)
            cv2.addWeighted(overlay, 0.35, frame, 1.0, 0, frame)

            # 4. Energy burst on first frame
            if not self._burst_done:
                self.energy_burst(x, y)

        # 5. Heart particles
        layer = np.zeros_like(frame)
        alive = []
        for hp in self._hearts:
            hp.update()
            if hp.alive():
                hp.draw(layer)
                alive.append(hp)
        self._hearts = alive
        cv2.add(frame, layer, frame)

        # 6. Text + timer
        self._text.update()
        self._text.draw(frame)
