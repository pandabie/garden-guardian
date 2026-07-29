"""Small helpers for Garden Guardian Phase 1."""

from collections import Counter
from pathlib import Path

import yaml

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def load_class_names(data_yaml: str | Path) -> dict[int, str]:
    """Read class id -> name mapping from data.yaml."""
    with open(data_yaml, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return {int(k): v for k, v in cfg["names"].items()}


def dataset_summary(split_dir: str | Path) -> None:
    """Print image count and label distribution for one split (e.g. data/train).

    Useful before training: catches empty labels and class imbalance early.
    """
    split_dir = Path(split_dir)
    images = [p for p in (split_dir / "images").glob("*") if p.suffix.lower() in IMG_EXTS]
    labels = list((split_dir / "labels").glob("*.txt"))

    class_counts: Counter[int] = Counter()
    empty = 0
    for lbl in labels:
        lines = [ln for ln in lbl.read_text().splitlines() if ln.strip()]
        if not lines:
            empty += 1
        for ln in lines:
            class_counts[int(ln.split()[0])] += 1

    print(f"[{split_dir}]")
    print(f"  images: {len(images)}  labels: {len(labels)}  empty labels: {empty}")
    print(f"  boxes per class: {dict(sorted(class_counts.items()))}")
    if len(images) != len(labels):
        print("  ⚠ image/label count mismatch — check your export from Roboflow")


if __name__ == "__main__":
    for split in ("data/train", "data/valid", "data/test"):
        if Path(split).exists():
            dataset_summary(split)
