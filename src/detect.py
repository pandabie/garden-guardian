"""Garden Guardian — Phase 1 crop detector.

Runs a trained YOLOv8 model on an image (or folder of images) and saves
an annotated copy with green boxes around detected crops.

Usage:
    python src/detect.py --weights best.pt --source garden.jpg
    python src/detect.py --weights best.pt --source photos/ --conf 0.5
"""

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Detect cultivated crops in garden photos.")
    p.add_argument("--weights", type=str, required=True, help="Path to trained .pt weights")
    p.add_argument("--source", type=str, required=True, help="Image file or folder")
    p.add_argument(
        "--conf",
        type=float,
        default=0.5,
        help="Confidence threshold. Detections below this are ignored. "
        "Keep it fairly high: a crop the model is unsure about must NOT "
        "be treated as a weed downstream.",
    )
    p.add_argument("--out", type=str, default="runs/predict", help="Output directory")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.weights)

    results = model.predict(
        source=args.source,
        conf=args.conf,
        save=True,
        project=str(Path(args.out).parent),
        name=Path(args.out).name,
        exist_ok=True,
    )

    for r in results:
        n = len(r.boxes)
        names = [model.names[int(c)] for c in r.boxes.cls]
        print(f"{Path(r.path).name}: {n} crop(s) detected -> {names}")

    print(f"\nAnnotated images saved to: {args.out}/")
    print("Safety rule: anything NOT boxed is a removal candidate, "
          "but low-confidence regions should never be touched.")


if __name__ == "__main__":
    main()
