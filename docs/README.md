# 🎬 Cinematic Hand Tracking FX

> Real-time hand tracking dengan efek visual sinematik ala TikTok — 100% offline, berbasis webcam lokal.

---

## ✨ Demo Gesture & Efek

| Gesture | Mode | Efek Visual |
|---|---|---|
| ✊ **Fist** | CLEAR | Reset semua efek |
| ✌ **Peace** (2 jari) | DRAW | Trail warna-warni mengikuti jari |
| ✋ **Open Hand** (5 jari) | FIRE 🔥 | Api muncul dari semua ujung jari |
| ☝ **Pointing** (telunjuk) | LASER ⚡ | Laser neon dari ujung telunjuk |
| 👍 **Thumbs Up** | FOLLOW | Bola neon mengikuti jari dengan easing |
| 🤟 **ILY** (jempol+telunjuk+kelingking) | I LOVE YOU 💜 | Mode sinematik penuh |
| Gerakan cepat | AUTO | Lightning bolt otomatis! |

### 💜 ILY Mode — Detail Efek
- Background digelapkan otomatis
- Zoom sinematik halus
- Aura neon berdenyut: **pink → ungu → biru**
- Partikel hati melayang naik
- Energy burst saat pertama aktif
- Teks "I LOVE YOU ❤" beranimasi pulsing

---

## 🚀 Cara Install & Jalankan

### 1. Persyaratan
- Python **3.10+**
- Webcam (built-in atau eksternal)
- RAM minimal 4 GB

### 2. Clone / ekstrak project
```bash
# Jika dari zip:
unzip cinematic_hand_fx.zip
cd cinematic_hand_fx
```

### 3. (Opsional) Buat virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Jalankan!
```bash
python main.py
```

> Model MediaPipe (~8 MB) akan otomatis diunduh saat pertama kali dijalankan.

---

## 🎮 Kontrol

| Tombol | Aksi |
|---|---|
| **Q** atau **ESC** | Keluar |

Semua kontrol lainnya melalui **gesture tangan** — lihat tabel di atas.

---

## ⚙️ Konfigurasi (`config.py`)

Semua parameter dapat diubah di `config.py` tanpa menyentuh kode utama:

```python
# Smoothing
EMA_ALPHA = 0.40        # 0.1 = sangat halus, 0.9 = sangat responsif
POINTER_HISTORY = 8     # Window rolling average

# Gesture stability
GESTURE_BUFFER_SIZE = 10    # Frame untuk majority voting
GESTURE_COOLDOWN_SEC = 0.3  # Jeda min antar ganti mode

# Performance
CAM_WIDTH = 1280        # Resolusi kamera
DETECT_WIDTH = 640      # Resolusi deteksi (lebih kecil = lebih cepat)
TARGET_FPS = 30

# Effects
PARTICLE_MAX = 800      # Maks partikel aktif
LASER_LENGTH = 300      # Panjang laser (px)
LIGHTNING_THRESHOLD_VEL = 18.0  # Kecepatan untuk trigger lightning

# ILY Mode
ILY_BG_DARKEN = 0.55    # 0 = hitam total, 1 = normal
ILY_ZOOM_FACTOR = 1.08  # 1.0 = tidak zoom

# Rendering
BLOOM_INTENSITY = 0.45
COLOR_GRADE_SATURATION = 1.3
COLOR_GRADE_VIGNETTE = 0.6
```

---

## 📂 Struktur Project

```
cinematic_hand_fx/
├── main.py                 ← Entry point utama
├── config.py               ← Semua parameter tunable
├── requirements.txt
│
├── core/
│   ├── hand_tracker.py     ← MediaPipe + threaded camera
│   ├── gesture_smoother.py ← EMA smoothing + velocity tracking
│   ├── gesture_detector.py ← Buffer 10 frame + majority voting
│   └── motion.py           ← Analisis kecepatan gerak
│
├── effects/
│   ├── particle.py         ← Sistem partikel HSV
│   ├── trail.py            ← Trail smooth dengan interpolasi
│   ├── glow.py             ← Glow halo + aura berdenyut
│   ├── laser.py            ← Laser neon dari jari
│   ├── fire.py             ← Api dari ujung jari
│   ├── lightning.py        ← Lightning bolt rekursif
│   └── ily.py              ← Mode ILY lengkap
│
├── rendering/
│   ├── bloom.py            ← Bloom post-process
│   ├── motion_blur.py      ← Motion blur berbasis kecepatan
│   └── color_grading.py    ← Neon color grade + vignette
│
├── ui/
│   └── overlay.py          ← HUD (FPS, mode badge, guide bar)
│
└── docs/
    └── README.md           ← Dokumentasi ini
```

---

## 🧠 Arsitektur Pipeline

```
Webcam (threaded)
    ↓
Hand Detection (MediaPipe, downscaled 640×360)
    ↓
EMA Smoother (α=0.4) + Velocity Tracker
    ↓
Gesture Detector (10-frame buffer + majority vote)
    ↓
Effect Engine
  ├── DRAWING  → DrawingCanvas + Trail
  ├── FIRE     → FireEffect (5 fingertips) + Trail + Lightning (auto)
  ├── LASER    → LaserEffect (index direction)
  ├── FOLLOW   → FollowBall (easing) + Lightning (auto)
  └── ILY      → ILYEffect (dark bg + zoom + aura + hearts)
    ↓
Rendering Pipeline
  1. Bloom      (bright pixels → blur → additive blend)
  2. MotionBlur (velocity-driven temporal blend)
  3. ColorGrade (saturation + contrast + vignette)
    ↓
HUD Overlay (FPS, mode, confidence bar, guide)
    ↓
cv2.imshow → ≥30 FPS
```

---

## 🔧 Troubleshooting

**Kamera tidak terbuka:**
```python
# Di config.py, ubah:
CAM_INDEX = 1   # coba 1, 2, dst
```

**FPS rendah (< 20):**
```python
# Di config.py, kurangi resolusi:
CAM_WIDTH    = 640
CAM_HEIGHT   = 480
DETECT_WIDTH = 320
DETECT_HEIGHT = 180

# Matikan color grading:
COLOR_GRADE_ENABLED = False
```

**MediaPipe gagal install (macOS M1/M2):**
```bash
pip install mediapipe --no-binary mediapipe
```

**Model tidak bisa diunduh otomatis:**
```
Download manual:
https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task

Simpan sebagai: hand_landmarker.task (di folder project)
```

**Gesture tidak terbaca / sering salah:**
- Pastikan pencahayaan cukup (tidak backlit)
- Jarak tangan 30–70 cm dari kamera
- Background kontras (hindari latar ramai)
- Satu tangan saja di frame

---

## 🖥️ Persyaratan Sistem

| Komponen | Minimum | Rekomendasi |
|---|---|---|
| Python | 3.10 | 3.11+ |
| RAM | 4 GB | 8 GB |
| CPU | Dual-core 2 GHz | Quad-core 3 GHz |
| Webcam | 720p | 1080p |
| OS | Win 10 / Ubuntu 20 / macOS 11 | |

---

## 🎨 Teknologi

- **OpenCV** — frame processing, rendering, compositing
- **MediaPipe** — 21 hand landmark detection
- **NumPy** — array ops, HSV color math
- **Python threading** — camera reader tanpa lag buffer

---

*Made with 💜 — 100% offline, no internet required after model download.*
