import tempfile
import unittest
from pathlib import Path

from src.policy import Detection, SafetyPolicy


class SafetyPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = SafetyPolicy(
            crop_classes=frozenset({"tomato"}),
            target_weed_classes=frozenset({"dandelion"}),
            model_confidence=0.20,
            weed_candidate_confidence=0.85,
            crop_exclusion_margin_px=10,
        )

    def test_crop_is_protected(self):
        result = self.policy.decide([Detection("tomato", 0.30, (10, 10, 30, 30))])
        self.assertEqual(result[0].recommendation, "protect")

    def test_known_high_confidence_weed_is_candidate(self):
        result = self.policy.decide(
            [Detection("dandelion", 0.95, (100, 100, 130, 130))]
        )
        self.assertEqual(result[0].recommendation, "removal_candidate")

    def test_low_confidence_weed_needs_review(self):
        result = self.policy.decide(
            [Detection("dandelion", 0.70, (100, 100, 130, 130))]
        )
        self.assertEqual(result[0].reason, "weed_confidence_too_low")

    def test_weed_near_crop_needs_review(self):
        result = self.policy.decide(
            [
                Detection("tomato", 0.40, (10, 10, 30, 30)),
                Detection("dandelion", 0.95, (35, 10, 50, 30)),
            ]
        )
        self.assertEqual(result[1].reason, "inside_crop_safety_zone")

    def test_unconfigured_model_class_needs_review(self):
        result = self.policy.decide(
            [Detection("mystery_plant", 0.99, (100, 100, 130, 130))]
        )
        self.assertEqual(result[0].reason, "unconfigured_class")

    def test_yaml_rejects_overlapping_roles(self):
        config = """
classes:
  crops: [tomato]
  target_weeds: [tomato]
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "policy.yaml"
            path.write_text(config, encoding="utf-8")
            with self.assertRaises(ValueError):
                SafetyPolicy.from_yaml(path)


if __name__ == "__main__":
    unittest.main()
