"""
main.py — Cinematic Hand Tracking FX
=====================================
Pipeline: camera → tracking → EMA smooth → gesture detect →
          effects → bloom → motion blur → color grade → UI → display

Gestures:
  ✊ Fist        → CLEAR all effects
  ✌ Peace       → DRAWING mode  (index+middle trail)
  ✋ Open Hand   → FIRE mode     (fire from all fingertips)
  ☝ Pointing    → LASER mode    (neon beam from index)
  👍 Thumbs Up  → FOLLOW mode   (glowing ball follows tip)
  🤟 ILY        → ILY mode      (cinematic love burst)
  Fast move     → LIGHTNING     (auto-triggered by velocity)
  Q / ESC       → Quit
"""

import sys
import time
from collections import deque

import cv2
import numpy as np

# ── Project imports ───────────────────────────────────────────────────────────
import config
from core      import (HandTracker, CameraReader,
                       HAND_CONNECTIONS, FINGERTIP_INDICES,
                       GestureSmoother, GestureDetector, MotionTracker)
from effects   import (ParticleSystem, TrailEffect, AuraEffect, draw_glow,
                       LaserEffect, FireEffect, LightningEffect, ILYEffect)
from rendering import BloomPass, MotionBlurPass, ColorGradingPass
from ui        import HUDOverlay


# ── Follow ball helper ────────────────────────────────────────────────────────
class FollowBall:
    def __init__(self, W: int, H: int):
        self.x  = float(W // 2)
        self.y  = float(H // 2)
        self.tx = self.x
        self.ty = self.y
        self._ease = 0.14
        self._hue  = 0
        self._trail = deque(maxlen=20)

    def update(self, tx: int, ty: int):
        self.tx, self.ty = tx, ty
        self._trail.append((int(self.x), int(self.y)))
        self.x += (self.tx - self.x) * self._ease
        self.y += (self.ty - self.y) * self._ease
        self._hue = (self._hue + 2) % 180

    def draw(self, frame: np.ndarray):
        n = len(self._trail)
        for i, (px, py) in enumerate(self._trail):
            a   = (i + 1) / n if n else 1.0
            r   = max(1, int(16 * a * 0.55))
            bgr = cv2.cvtColor(
                np.uint8([[[self._hue, 210, int(255 * a)]]]),
                cv2.COLOR_HSV2BGR)[0][0].tolist()
            cv2.circle(frame, (px, py), r, bgr, -1)
        # Main ball
        bgr = cv2.cvtColor(
            np.uint8([[[self._hue, 255, 255]]]),
            cv2.COLOR_HSV2BGR)[0][0].tolist()
        cx, cy = int(self.x), int(self.y)
        ov = frame.copy()
        cv2.circle(ov, (cx, cy), 28, bgr, -1)
        cv2.addWeighted(ov, 0.25, frame, 0.75, 0, frame)
        cv2.circle(frame, (cx, cy), 20, bgr, -1)
        cv2.circle(frame, (cx, cy), 20, (255, 255, 255), 2)
        cv2.circle(frame, (cx - 7, cy - 7), 5, (255, 255, 255), -1)


# ── Drawing canvas helper ─────────────────────────────────────────────────────
class DrawingCanvas:
    def __init__(self, H: int, W: int):
        self._canvas  = np.zeros((H, W, 3), dtype=np.uint8)
        self._prev_pt = None
        self._hue     = 0

    def add_point(self, x: int | None, y: int | None):
        if x is None or y is None:
            self._prev_pt = None
            return
        self._hue = (self._hue + 1) % 180
        bgr = cv2.cvtColor(
            np.uint8([[[self._hue, 240, 255]]]),
            cv2.COLOR_HSV2BGR)[0][0].tolist()
        if self._prev_pt is not None:
            cv2.line(self._canvas, self._prev_pt, (x, y), bgr, 4, cv2.LINE_AA)
        self._prev_pt = (x, y)

    def blend_onto(self, frame: np.ndarray):
        if not np.any(self._canvas):
            return
        blur = cv2.GaussianBlur(self._canvas, (7, 7), 0)
        glow = cv2.addWeighted(self._canvas, 1.0, blur, 0.5, 0)
        mask = np.any(self._canvas > 0, axis=2)
        frame[mask] = cv2.addWeighted(glow, 0.88, frame, 0.12, 0)[mask]

    def clear(self):
        self._canvas[:] = 0
        self._prev_pt   = None


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Cinematic Hand Tracking FX")
    print("=" * 60)

    # Camera
    cam = CameraReader(src=config.CAM_INDEX,
                       w=config.CAM_WIDTH, h=config.CAM_HEIGHT)
    if not cam.cap.isOpened():
        print("[ERROR] Cannot open webcam. Try changing CAM_INDEX in config.py")
        sys.exit(1)
    W, H = cam.size()
    print(f"[Camera] {W}x{H} @ {config.TARGET_FPS} FPS")

    # Core
    tracker  = HandTracker()
    smoother = GestureSmoother(alpha=config.EMA_ALPHA)
    detector = GestureDetector()
    motion   = MotionTracker()

    # Effects
    particles = ParticleSystem()
    trail     = TrailEffect()
    fire_fx   = FireEffect()
    laser_fx  = LaserEffect()
    lightning = LightningEffect()
    ily_fx    = ILYEffect(W, H)
    aura_fx   = AuraEffect()
    ball      = FollowBall(W, H)
    canvas    = DrawingCanvas(H, W)

    # Rendering
    bloom      = BloomPass()
    mblur      = MotionBlurPass()
    color_grade = ColorGradingPass()

    # UI
    hud = HUDOverlay(W, H)

    # State
    mode        = "IDLE"
    gesture     = "OTHER"
    confidence  = 0.0
    fx: int | None = None
    fy: int | None = None
    prev_fx: int | None = None
    prev_fy: int | None = None

    fps_deque = deque(maxlen=30)
    prev_time = time.time()
    disp_fps  = 0.0

    frame_delay = max(1, int(1000 / config.TARGET_FPS))

    print("\nReady! Show your hand to the camera.")
    print("Gestures: ✊ CLEAR | ✌ DRAW | ✋ FIRE | ☝ LASER | 👍 FOLLOW | 🤟 ILY | Q QUIT\n")

    while True:
        # ── 1. Grab frame ─────────────────────────────────────────────────────
        ret, frame = cam.read()
        if not ret or frame is None:
            time.sleep(0.005)
            continue

        frame = cv2.flip(frame, 1)
        H, W  = frame.shape[:2]   # update in case window resized

        # ── 2. Track hand ─────────────────────────────────────────────────────
        result = tracker.detect(frame)
        hand_detected = result['detected']

        fx, fy = None, None

        if hand_detected:
            lms       = result['landmarks']
            hand_lbl  = result['hand_label']
            pts_full  = result['pts_full']

            # EMA-smooth index fingertip (landmark 8)
            raw_x = pts_full[8][0]
            raw_y = pts_full[8][1]
            smoother.update(raw_x, raw_y)
            fx, fy = smoother.get()

            # Motion / velocity
            motion.update(fx, fy)
            speed = motion.speed()

            # Gesture
            gesture, confidence = detector.update(lms, hand_lbl)

            # Skeleton
            if config.SHOW_SKELETON:
                hud.draw_skeleton(frame, pts_full,
                                  HAND_CONNECTIONS, FINGERTIP_INDICES)
        else:
            smoother.reset()
            detector.reset()
            motion.reset()
            speed = 0.0
            gesture = "OTHER"
            confidence = 0.0

        # ── 3. Mode switching from gesture ────────────────────────────────────
        if gesture == "FIST":
            if mode != "IDLE":
                mode = "IDLE"
                particles.clear()
                fire_fx.clear()
                lightning.clear()
                canvas.clear()
                trail.clear()
                ily_fx.deactivate()
        elif gesture == "PEACE":
            mode = "DRAWING"
            ily_fx.deactivate()
        elif gesture == "OPEN_HAND":
            mode = "FIRE"
            ily_fx.deactivate()
        elif gesture == "POINTING":
            mode = "LASER"
            ily_fx.deactivate()
        elif gesture == "THUMBS_UP":
            mode = "FOLLOW"
            ily_fx.deactivate()
        elif gesture == "ILY":
            if mode != "ILY":
                mode = "ILY"
                ily_fx.activate()

        # Auto-lightning: fast movement in FIRE or FOLLOW mode
        if (speed > config.LIGHTNING_THRESHOLD_VEL
                and mode in ("FIRE", "FOLLOW")
                and fx is not None and fy is not None
                and prev_fx is not None and prev_fy is not None):
            lightning.trigger(prev_fx, prev_fy, fx, fy)

        # ── 4. Effect logic ───────────────────────────────────────────────────
        if fx is not None and fy is not None:
            if mode == "DRAWING":
                canvas.add_point(fx, fy)
                trail.update(fx, fy)

            elif mode == "FIRE":
                fire_fx.update(pts_full if hand_detected else None)
                trail.update(fx, fy)

            elif mode == "LASER":
                # laser drawn later; add subtle trail
                trail.update(fx, fy)

            elif mode == "FOLLOW":
                ball.update(fx, fy)

            elif mode == "ILY":
                ily_fx.emit_hearts(fx, fy)
                # Slow-motion: emit fewer particles
                if int(time.time() * 10) % 3 == 0:
                    particles.emit(fx, fy, count=2, hue_range=(140, 170))

        else:
            if mode == "DRAWING":
                canvas.add_point(None, None)
            trail.update(None, None)

        prev_fx, prev_fy = fx, fy

        # ── 5. Render effects ─────────────────────────────────────────────────

        # Drawing canvas glow
        canvas.blend_onto(frame)

        # Trail
        trail.draw(frame)

        # Fire
        fire_fx.draw(frame)

        # Laser (pointing mode)
        if mode == "LASER" and hand_detected:
            laser_fx.draw(frame, pts_full)

        # Particles
        particles.update_and_draw(frame)

        # Follow ball
        if mode == "FOLLOW":
            ball.draw(frame)

        # Lightning
        lightning.update_and_draw(frame)

        # ILY mode (dark bg, aura, hearts, text) — applied over everything
        if mode == "ILY":
            ily_fx.draw(frame, fx, fy)

        # Glow dot at finger tip
        if fx is not None and fy is not None and mode != "ILY":
            draw_glow(frame, fx, fy,
                      config.MODE_COLORS.get(mode, (255, 255, 255)),
                      radius=14)
            hud.draw_finger_dot(frame, fx, fy, mode)

        # ── 6. Post-processing pipeline ───────────────────────────────────────
        # Bloom
        frame = bloom.apply(frame)

        # Motion blur (velocity-driven)
        frame = mblur.apply(frame, velocity=speed if hand_detected else 0.0)

        # Color grading
        if config.COLOR_GRADE_ENABLED:
            frame = color_grade.apply(frame)

        # ── 7. HUD ────────────────────────────────────────────────────────────
        now       = time.time()
        dt        = max(now - prev_time, 1e-6)
        prev_time = now
        fps_deque.append(1.0 / dt)
        disp_fps = sum(fps_deque) / len(fps_deque)

        hud.draw(frame, disp_fps, mode, hand_detected, confidence)

        # ── 8. Display ────────────────────────────────────────────────────────
        cv2.imshow("Cinematic Hand Tracking FX", frame)
        key = cv2.waitKey(frame_delay) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break

    # Cleanup
    cam.release()
    tracker.close()
    cv2.destroyAllWindows()
    print("Bye! 👋")


if __name__ == "__main__":
    main()
