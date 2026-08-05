# 🌿 Garden Guardian

> A safety-first perception and decision system for a backyard weeding robot.

Garden Guardian is being built as the brain of a low, round robot that drives
itself across the lawn like a robot vacuum. Phase 1 recognizes both cultivated
crops and selected weed species, then turns detections into safe
recommendations. It does **not** control a motor, cutter, or sprayer yet.

## Decision model

The model learns a small, explicit set of plants:

```
known crop       -> protect
known target weed + high confidence + far from crop -> removal candidate
low confidence / unconfigured class / near crop     -> human review
not detected                                             -> no action
```

`removal_candidate` is deliberately not an actuator command. Image coordinates
must first be calibrated into ground-plane distances, the robot must know where
it currently is, and a separate hardware safety layer must approve any physical
action.

## 🗺️ Roadmap

| Phase | Goal | Status |
|---|---|---|
| **1** | Detect crops and target weeds → safe recommendations | 🚧 In progress |
| **2** | Ground-plane calibration: pixel → cm via homography | ⬜ Planned |
| **3** | Coverage map: track scanned vs unscanned ground | ⬜ Planned |
| **4** | Edge deployment (Raspberry Pi / Jetson) | ⬜ Planned |
| **5** | Mobile base integration + hardware safety controller | ⬜ Planned |

## 🚀 Quick Start (Phase 1)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Choose the plants

Edit both files before labeling any photos:

- `data/data.yaml`: every class the model will learn
- `config/garden.yaml`: which classes are crops and which are target weeds

The example configuration contains tomato, basil, lettuce, dandelion, and
crabgrass. Replace these with plants actually found in your garden.

### 3. Build the dataset

Label **every visible instance** of the configured crops and target weeds in
Roboflow, export in YOLO format, and place it under `data/`:


```
data/
├── data.yaml
├── train/images  train/labels
├── valid/images  valid/labels
└── test/images   test/labels
```

Dataset images are ignored by Git. Before training, check the export:

```bash
python src/utils.py
```

### 4. Train

```bash
yolo detect train data=data/data.yaml model=yolov8n.pt epochs=100 imgsz=640
```

Or open `notebooks/01_train.ipynb` for a guided walkthrough.

### 5. Observe (safe default)

```bash
python src/detect.py --weights runs/detect/train/weights/best.pt --source path/to/photo.jpg
```

Outputs are saved under `runs/observe/`:

- annotated images: green = protect, red = removal candidate, amber = review
- `decisions.json`: structured image-pixel coordinates for the future planner
- `actuation_authorized: false`: an explicit guard against treating the report
  as permission to activate hardware

Example detection in the report:

```json
{
  "class_name": "dandelion",
  "confidence": 0.94,
  "bbox": [120.0, 80.0, 210.0, 190.0],
  "recommendation": "removal_candidate",
  "reason": "known_weed_above_confidence_threshold"
}
```

## Safety boundaries

- Unknown objects cannot be discovered merely because they have no box. An
  unboxed region always means **no action**, never “weed”.
- A target weed needs a higher confidence than ordinary observation.
- A configurable exclusion zone around every detected crop blocks candidates.
- This cannot protect a crop that the model completely misses. Real-world use
  therefore requires representative data, validation, calibration, and a
  physical emergency stop.
- The base is mobile, so there is no fixed origin to fall back on. Until the
  robot can reliably estimate its own position, every recommendation is valid
  only for the frame it was computed from.
- Start in observe-only mode and review results before designing actuation.

Adjust thresholds and class roles in `config/garden.yaml`. Keep the model
confidence low enough to notice uncertain crops; keep the weed-candidate
confidence conservative.

## Tests

```bash
python -m unittest discover -s tests -v
```

## 🛠️ Stack

Python · [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) · OpenCV · Roboflow (labeling)

## 📄 License

MIT
