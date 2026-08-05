"""Run crop/weed perception and emit safe robot-brain recommendations.

The JSON output is intentionally non-actuating. ``removal_candidate`` means
"consider this target after calibration and hardware safety checks", never
"activate a tool now".
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import cv2
from ultralytics import YOLO

from policy import Decision, Detection, SafetyPolicy


COLORS = {
    "protect": (60, 190, 80),
    "removal_candidate": (50, 50, 230),
    "review": (0, 180, 255),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect crops and target weeds without controlling hardware."
    )
    parser.add_argument("--weights", required=True, help="Trained YOLO .pt weights")
    parser.add_argument("--source", required=True, help="Image, folder, or camera source")
    parser.add_argument(
        "--policy", default="config/garden.yaml", help="Garden safety-policy YAML"
    )
    parser.add_argument("--out", default="runs/observe", help="Output directory")
    parser.add_argument(
        "--conf",
        type=float,
        default=None,
        help="Override model confidence from the policy (normally omit this)",
    )
    return parser.parse_args()


def _model_name(names: dict | list, class_id: int) -> str:
    return str(names[class_id])


def _extract_detections(result, names: dict | list) -> list[Detection]:
    detections: list[Detection] = []
    for box in result.boxes:
        class_id = int(box.cls.item())
        coordinates = tuple(float(value) for value in box.xyxy[0].tolist())
        detections.append(
            Detection(
                class_name=_model_name(names, class_id),
                confidence=float(box.conf.item()),
                bbox=coordinates,
            )
        )
    return detections


def _annotate(image, decisions: list[Decision]):
    annotated = image.copy()
    for item in decisions:
        x1, y1, x2, y2 = (round(value) for value in item.bbox)
        color = COLORS[item.recommendation]
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"{item.class_name} {item.confidence:.2f} | {item.recommendation}"
        cv2.putText(
            annotated,
            label,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
    return annotated


def main() -> None:
    args = parse_args()
    policy = SafetyPolicy.from_yaml(args.policy)
    confidence = policy.model_confidence if args.conf is None else args.conf
    if not 0 <= confidence <= 1:
        raise ValueError("--conf must be between 0 and 1")

    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(args.weights)
    results = model.predict(source=args.source, conf=confidence, save=False)
    report = {
        "schema_version": 1,
        "actuation_authorized": False,
        "coordinate_system": "image_pixels_xyxy",
        "policy": str(Path(args.policy)),
        "frames": [],
    }

    for index, result in enumerate(results):
        detections = _extract_detections(result, model.names)
        decisions = policy.decide(detections)
        source_path = Path(str(result.path))
        output_name = f"{source_path.stem}_{index:04d}{source_path.suffix or '.jpg'}"
        output_path = output_dir / output_name
        if not cv2.imwrite(str(output_path), _annotate(result.orig_img, decisions)):
            raise OSError(f"Could not save annotated image: {output_path}")

        counts = Counter(item.recommendation for item in decisions)
        report["frames"].append(
            {
                "source": str(source_path),
                "annotated_image": str(output_path),
                "summary": dict(counts),
                "detections": [item.to_dict() for item in decisions],
            }
        )
        print(f"{source_path.name}: {dict(counts)}")

    report_path = output_dir / "decisions.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Annotated images and recommendations saved to: {output_dir}")
    print("Physical actuation is NOT authorized by this output.")


if __name__ == "__main__":
    main()
