import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.services.classifier import classify_event


class ClassifierTests(unittest.TestCase):
    def test_time_trial_excluded(self):
        result = classify_event({"format": "time_trial"})
        self.assertEqual(result["event_tier"], "E0")

    def test_penalties_off_caps(self):
        result = classify_event(
            {
                "format": "endurance",
                "duration": 120,
                "grid": 30,
                "classes": 2,
                "damage": "off",
                "penalties": "off",
                "fuel": "real",
                "tire": "real",
                "schedule": "weekly",
                "license": "intermediate",
                "stewarding": "automated",
                "official": True,
            }
        )
        self.assertEqual(result["event_tier"], "E1")
        self.assertIn("penalties_or_damage_off", result["caps_applied"])


if __name__ == "__main__":
    unittest.main()