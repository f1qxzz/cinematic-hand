"""
ui/overlay.py — Cinematic HUD overlay.
Draws: FPS counter, mode badge, confidence bar, gesture guide.
"""

import math
import time
import numpy as np
import cv2
import config


class HUDOverlay:
    def __init__(self, W: int, H: int):
        self.W = W
        self.H = H
        self._hue = 0

    # ── Top bar ───────────────────────────────────────────────────────────────
    def _draw_top_bar(self, frame: np.ndarray, fps: float,
                      mode: str, hand_detected: bool, confidence: float):
        bar = frame.copy()
        cv2.rectangle(bar, (0, 0), (self.W, 60), (6, 6, 16), -1)
        cv2.addWeighted(bar, 0.72, frame, 0.28, 0, frame)

        # Thin accent line under bar
        accent = config.MODE_COLORS.get(mode, (140, 140, 140))
        cv2.line(frame, (0, 60), (self.W, 60), accent, 1)

        # FPS — left
        fps_col = (60, 255, 80) if fps >= 25 else (0, 120, 255)
        cv2.putText(frame, f"FPS {fps:4.1f}", (14, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, fps_col, 2, cv2.LINE_AA)

        # Mode badge — centre
        label = config.MODE_LABELS.get(mode, mode)
        text  = f"[ {label} ]"
        (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        cv2.putText(frame, text,
                    (self.W // 2 - tw // 2, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, accent, 2, cv2.LINE_AA)

        # Hand status — right
        if hand_detected:
            status, s_col = "HAND ON", (0, 255, 120)
        else:
            status, s_col = "NO HAND", (60, 60, 220)
        (sw, _), _ = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        cv2.putText(frame, status, (self.W - sw - 14, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, s_col, 2, cv2.LINE_AA)

        # Confidence mini-bar (right side, under status)
        if hand_detected and confidence > 0:
            bx = self.W - sw - 14
            by = 50
            bw = sw
            cv2.rectangle(frame, (bx, by), (bx + bw, by + 4), (40, 40, 40), -1)
            cv2.rectangle(frame, (bx, by),
                          (bx + int(bw * confidence), by + 4),
                          s_col, -1)

    # ── Bottom guide bar ──────────────────────────────────────────────────────
    def _draw_guide_bar(self, frame: np.ndarray):
        gb = frame.copy()
        cv2.rectangle(gb, (0, self.H - 48), (self.W, self.H),
                      (6, 6, 16), -1)
        cv2.addWeighted(gb, 0.62, frame, 0.38, 0, frame)
        cv2.line(frame, (0, self.H - 48), (self.W, self.H - 48),
                 (50, 50, 80), 1)

        guide = (
            "  ✊ CLEAR  |  ✌ DRAW  |  ✋ FIRE  |"
            "  ☝ LASER  |  👍 FOLLOW  |  🤟 ILY  |  Q / ESC: QUIT"
        )
        cv2.putText(frame, guide, (8, self.H - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40,
                    (170, 170, 200), 1, cv2.LINE_AA)

    # ── Finger dot ────────────────────────────────────────────────────────────
    def draw_finger_dot(self, frame: np.ndarray, x: int, y: int, mode: str):
        col   = config.MODE_COLORS.get(mode, (255, 255, 255))
        pulse = int(abs(math.sin(time.time() * 6)) * 7)

        overlay = frame.copy()
        cv2.circle(overlay, (x, y), 20 + pulse, col, 2)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        cv2.circle(frame, (x, y), 9, col, -1)
        cv2.circle(frame, (x, y), 9, (255, 255, 255), 1)

    # ── Hand skeleton ─────────────────────────────────────────────────────────
    def draw_skeleton(self, frame: np.ndarray, pts_full: list,
                      connections: list, tip_indices: set):
        for a, b in connections:
            cv2.line(frame, pts_full[a], pts_full[b],
                     (40, 160, 40), 2, cv2.LINE_AA)
        for i, (px, py) in enumerate(pts_full):
            if i in tip_indices:
                cv2.circle(frame, (px, py), 6, (0, 255, 100), -1)
                cv2.circle(frame, (px, py), 6, (255, 255, 255), 1)
            else:
                cv2.circle(frame, (px, py), 3, (160, 160, 160), -1)

    # ── Main draw call ────────────────────────────────────────────────────────
    def draw(self, frame: np.ndarray, fps: float, mode: str,
             hand_detected: bool, confidence: float = 0.0):
        self._draw_top_bar(frame, fps, mode, hand_detected, confidence)
        if config.SHOW_GUIDE_BAR:
            self._draw_guide_bar(frame)
