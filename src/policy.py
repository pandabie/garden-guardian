"""Safety policy for turning model detections into robot recommendations.

This module deliberately has no motor, sprayer, or cutter integration. It
produces recommendations only; a later coordinate-mapping and hardware safety
layer must authorize physical movement.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import yaml


BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class Detection:
    """One model detection in image-pixel coordinates (x1, y1, x2, y2)."""

    class_name: str
    confidence: float
    bbox: BBox


@dataclass(frozen=True)
class Decision:
    """A safe interpretation of a detection."""

    class_name: str
    confidence: float
    bbox: BBox
    recommendation: str
    reason: str

    def to_dict(self) -> dict:
        result = asdict(self)
        result["bbox"] = list(self.bbox)
        return result


@dataclass(frozen=True)
class SafetyPolicy:
    crop_classes: frozenset[str]
    target_weed_classes: frozenset[str]
    model_confidence: float = 0.20
    weed_candidate_confidence: float = 0.85
    crop_exclusion_margin_px: float = 40.0

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SafetyPolicy":
        with open(path, encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}

        classes = config.get("classes", {})
        safety = config.get("safety", {})
        policy = cls(
            crop_classes=frozenset(classes.get("crops", [])),
            target_weed_classes=frozenset(classes.get("target_weeds", [])),
            model_confidence=float(safety.get("model_confidence", 0.20)),
            weed_candidate_confidence=float(
                safety.get("weed_candidate_confidence", 0.85)
            ),
            crop_exclusion_margin_px=float(
                safety.get("crop_exclusion_margin_px", 40)
            ),
        )
        policy.validate()
        return policy

    def validate(self) -> None:
        overlap = self.crop_classes & self.target_weed_classes
        if overlap:
            raise ValueError(
                "Classes cannot be both crops and target weeds: "
                + ", ".join(sorted(overlap))
            )
        if not 0 <= self.model_confidence <= 1:
            raise ValueError("model_confidence must be between 0 and 1")
        if not 0 <= self.weed_candidate_confidence <= 1:
            raise ValueError("weed_candidate_confidence must be between 0 and 1")
        if self.weed_candidate_confidence < self.model_confidence:
            raise ValueError(
                "weed_candidate_confidence must be at least model_confidence"
            )
        if self.crop_exclusion_margin_px < 0:
            raise ValueError("crop_exclusion_margin_px cannot be negative")

    def decide(self, detections: Iterable[Detection]) -> list[Decision]:
        """Classify detections without ever authorizing physical actuation."""

        detections = list(detections)
        crop_boxes = [
            item.bbox for item in detections if item.class_name in self.crop_classes
        ]

        decisions: list[Decision] = []
        for item in detections:
            if item.class_name in self.crop_classes:
                decisions.append(_decision(item, "protect", "configured_crop"))
            elif item.class_name not in self.target_weed_classes:
                decisions.append(_decision(item, "review", "unconfigured_class"))
            elif item.confidence < self.weed_candidate_confidence:
                decisions.append(_decision(item, "review", "weed_confidence_too_low"))
            elif any(
                _intersects_with_margin(
                    item.bbox, crop_box, self.crop_exclusion_margin_px
                )
                for crop_box in crop_boxes
            ):
                decisions.append(_decision(item, "review", "inside_crop_safety_zone"))
            else:
                decisions.append(
                    _decision(
                        item,
                        "removal_candidate",
                        "known_weed_above_confidence_threshold",
                    )
                )
        return decisions


def _decision(item: Detection, recommendation: str, reason: str) -> Decision:
    return Decision(
        class_name=item.class_name,
        confidence=item.confidence,
        bbox=item.bbox,
        recommendation=recommendation,
        reason=reason,
    )


def _intersects_with_margin(candidate: BBox, protected: BBox, margin: float) -> bool:
    px1, py1, px2, py2 = protected
    ex1, ey1, ex2, ey2 = (
        px1 - margin,
        py1 - margin,
        px2 + margin,
        py2 + margin,
    )
    cx1, cy1, cx2, cy2 = candidate
    return cx1 <= ex2 and cx2 >= ex1 and cy1 <= ey2 and cy2 >= ey1
