# 🌿 Garden Guardian

> An autonomous weed-elimination robot for backyard gardens — built in phases, starting with crop detection.

<p align="center">
  <img src="docs/demo.jpg" alt="Crop detection demo" width="700"/>
  <br/>
  <em>Phase 1: YOLOv8 detecting cultivated crops. Anything outside a green box is a removal candidate.</em>
</p>

## 💡 Core Idea — Inverted Detection

Most weed-detection projects try to recognize **weeds** — but there are thousands of weed species, and datasets are scarce.

Garden Guardian flips the logic:

```
Old logic:  "This is a weed  → remove it"
Our logic:  "This is NOT a crop I planted → remove it"
```

Since the gardener knows exactly which crops they planted, the model only needs to learn a **small, closed set of classes**. Everything else is treated as a removal candidate — with a safety rule: **if uncertain, don't touch.**

## 🗺️ Roadmap

| Phase | Goal | Status |
|---|---|---|
| **1** | Crop Detector v0 — detect cultivated crops in photos | 🚧 In progress |
| **2** | Image-to-garden coordinate mapping (camera calibration) | ⬜ Planned |
| **3** | Edge deployment (Raspberry Pi / Jetson) | ⬜ Planned |
| **4** | Gantry drive system (X-Y rail, CNC-style) | ⬜ Planned |
| **5** | Targeted elimination head (spray / cut) | ⬜ Planned |

## 🚀 Quick Start (Phase 1)

### 1. Install

```bash
git clone https://github.com/<your-username>/garden-guardian.git
cd garden-guardian
pip install -r requirements.txt
```

### 2. Get the dataset

Dataset images are **not** stored in this repo (see `.gitignore`).
Labeled dataset is hosted on Roboflow: `<link coming soon>`

Expected layout after download:

```
data/
├── data.yaml
├── train/images  train/labels
├── valid/images  valid/labels
└── test/images   test/labels
```

### 3. Train

```bash
yolo detect train data=data/data.yaml model=yolov8n.pt epochs=100 imgsz=640
```

Or open `notebooks/01_train.ipynb` for a guided walkthrough.

### 4. Detect

```bash
python src/detect.py --weights runs/detect/train/weights/best.pt --source path/to/garden_photo.jpg
```

Output image with bounding boxes is saved to `runs/predict/`.

## 🧠 Design Decisions

- **Detect crops, not weeds** — small closed-set problem instead of open-world problem
- **YOLOv8n** — small enough to train on a consumer gaming laptop in <1 hour, and to later run on edge hardware
- **Gantry (rail) locomotion planned** — eliminates free navigation, the hardest robotics problem, entirely
- **Uncertainty = no action** — false negatives (missed weed) are cheap; false positives (destroyed crop) are expensive

## 📦 What's not in the repo

| Thing | Where it lives |
|---|---|
| Dataset images | Roboflow (link above) |
| Trained weights (`.pt`) | GitHub Releases |

## 🛠️ Stack

Python · [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) · OpenCV · Roboflow (labeling)

## 📄 License

MIT
