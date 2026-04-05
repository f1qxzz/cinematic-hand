"""
config.py — Cinematic Hand Tracking FX
Semua parameter tunable di satu tempat.
"""

# ── Camera ────────────────────────────────────────────────────────────────────
CAM_INDEX        = 0
CAM_WIDTH        = 1280
CAM_HEIGHT       = 720
TARGET_FPS       = 30
DETECT_WIDTH     = 640
DETECT_HEIGHT    = 360

# ── MediaPipe ────────────────────────────────────────────────────────────────
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)
MODEL_PATH = "hand_landmarker.task"
NUM_HANDS  = 1
MIN_DETECTION_CONF = 0.55
MIN_PRESENCE_CONF  = 0.55
MIN_TRACKING_CONF  = 0.45

# ── Smoothing (EMA) ──────────────────────────────────────────────────────────
EMA_ALPHA          = 0.40   # a in: smoothed = a*current + (1-a)*prev
VELOCITY_ALPHA     = 0.35   # EMA for velocity estimate
POINTER_HISTORY    = 8      # rolling avg window for pointer
INTERP_STEPS       = 3      # sub-frame interpolation steps

# ── Gesture Stability ────────────────────────────────────────────────────────
GESTURE_BUFFER_SIZE  = 10   # majority-vote window (frames)
GESTURE_THRESHOLD    = 7    # frames to confirm gesture
GESTURE_COOLDOWN_SEC = 0.3  # seconds between mode switches
GESTURE_CONFIDENCE_MIN = 0.6  # min vote ratio to accept

# ── Particle Effect ──────────────────────────────────────────────────────────
PARTICLE_COUNT_PER_FRAME = 6
PARTICLE_MAX             = 800
PARTICLE_GRAVITY         = 0.22

# ── Trail Effect ─────────────────────────────────────────────────────────────
TRAIL_MAX_LENGTH = 40
TRAIL_THICKNESS  = 3

# ── Glow / Aura ──────────────────────────────────────────────────────────────
GLOW_BLUR_KSIZE  = 25
GLOW_INTENSITY   = 0.6
AURA_RADIUS      = 60
AURA_PULSE_SPEED = 4.0

# ── Laser ─────────────────────────────────────────────────────────────────────
LASER_COLOR      = (0, 255, 255)
LASER_THICKNESS  = 2
LASER_LENGTH     = 300

# ── Fire ─────────────────────────────────────────────────────────────────────
FIRE_PARTICLE_COUNT = 8
FIRE_RISE_SPEED     = (-8, -3)
FIRE_SPREAD         = 30

# ── Lightning ─────────────────────────────────────────────────────────────────
LIGHTNING_SEGMENTS  = 12
LIGHTNING_DEVIATION = 28
LIGHTNING_THRESHOLD_VEL = 18.0   # px/frame velocity to trigger

# ── ILY Mode ─────────────────────────────────────────────────────────────────
ILY_SLOW_MOTION_FACTOR = 0.4     # 1.0 = normal, <1 = slower
ILY_BURST_PARTICLES    = 60
ILY_HEART_PER_FRAME    = 4
ILY_AURA_COLORS = [              # pink → purple → blue (HSV hue range)
    (160, 230, 255),
    (140, 220, 255),
    (120, 210, 255),
]
ILY_ZOOM_FACTOR        = 1.08   # subtle zoom
ILY_BG_DARKEN          = 0.55   # darken background coefficient

# ── Rendering Pipeline ───────────────────────────────────────────────────────
BLOOM_BLUR_KSIZE    = 21
BLOOM_THRESHOLD     = 200       # pixel brightness to bloom
BLOOM_INTENSITY     = 0.45

MOTION_BLUR_FRAMES  = 3         # frames to average for motion blur
MOTION_BLUR_ALPHA   = 0.45

COLOR_GRADE_ENABLED = True
COLOR_GRADE_SATURATION = 1.3    # >1 boosts saturation
COLOR_GRADE_CONTRAST   = 1.1    # >1 boosts contrast
COLOR_GRADE_VIGNETTE   = 0.6    # vignette strength (0=none, 1=full)

# ── UI ────────────────────────────────────────────────────────────────────────
SHOW_SKELETON    = True
SHOW_FPS         = True
SHOW_GUIDE_BAR   = True

MODE_COLORS = {
    "IDLE":     (140, 140, 140),
    "FIRE":     (0,   120, 255),
    "LASER":    (0,   255, 255),
    "DRAWING":  (0,   210, 100),
    "FOLLOW":   (200, 80,  255),
    "ILY":      (80,  80,  255),
    "LIGHTNING":(180, 180,  50),
}
MODE_LABELS = {
    "IDLE":      "IDLE",
    "FIRE":      "FIRE  ✋",
    "LASER":     "LASER  ☝",
    "DRAWING":   "DRAW  ✌",
    "FOLLOW":    "FOLLOW  👍",
    "ILY":       "I LOVE YOU  🤟",
    "LIGHTNING": "LIGHTNING  ⚡",
}
