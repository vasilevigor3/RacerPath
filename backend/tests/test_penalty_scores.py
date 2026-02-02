"""
Tests and test data for penalty/incident scores and situation table.

Table: Situation -> Incident -> Penalty with assigned scores (incident_score, penalty_score).
"""
import sys
from pathlib import Path

import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.penalties.scores import (
    PENALTY_TYPE_SCORES,
    DEFAULT_PENALTY_SCORE,
    get_score_for_penalty_type,
    SITUATION_INCIDENT_PENALTY,
)


# | Situation                           | Incident             | Penalty      | incident_score | penalty_score |
# | ----------------------------------- | -------------------- | ------------ | --------------- | -------------- |
# | Лёгкий боковой контакт              | Light contact        | ❌            | 2               | 0              |
# | Контакт → потеря позиции соперником | Causing disadvantage | +Time        | 4               | 6              |
# | Удар сзади (brake too late)         | Rear-end collision   | +Time / DT   | 5               | 6 or 8         |
# | Выдавливание за трассу              | Forcing off track    | +Time        | 4               | 6              |
# | Контакт → разворот соперника        | Causing spin         | +Time / DT   | 5               | 6 or 8         |
# | Контакт → сход соперника            | Causing retirement   | DT / Stop&Go | 6               | 8 or 10        |
# | Массовый завал                      | Multi-car incident   | DSQ / Grid   | 8               | 35             |
# | Netcode / racing incident           | Racing incident      | ❌            | 0               | 0              |
SITUATION_TABLE = [
    {
        "situation": "Лёгкий боковой контакт",
        "incident": "Light contact",
        "penalty": None,
        "incident_score": 2.0,
        "penalty_score": 0.0,
    },
    {
        "situation": "Контакт → потеря позиции соперником",
        "incident": "Causing disadvantage",
        "penalty": "time_penalty",
        "incident_score": 4.0,
        "penalty_score": 6.0,
    },
    {
        "situation": "Удар сзади (brake too late)",
        "incident": "Rear-end collision",
        "penalty": "time_penalty",  # or drive_through
        "incident_score": 5.0,
        "penalty_score": 6.0,
    },
    {
        "situation": "Выдавливание за трассу",
        "incident": "Forcing off track",
        "penalty": "time_penalty",
        "incident_score": 4.0,
        "penalty_score": 6.0,
    },
    {
        "situation": "Контакт → разворот соперника",
        "incident": "Causing spin",
        "penalty": "time_penalty",  # or drive_through
        "incident_score": 5.0,
        "penalty_score": 6.0,
    },
    {
        "situation": "Контакт → сход соперника",
        "incident": "Causing retirement",
        "penalty": "drive_through",  # or stop_and_go
        "incident_score": 6.0,
        "penalty_score": 8.0,
    },
    {
        "situation": "Массовый завал",
        "incident": "Multi-car incident",
        "penalty": "dsq",
        "incident_score": 8.0,
        "penalty_score": 35.0,
    },
    {
        "situation": "Netcode / racing incident",
        "incident": "Racing incident",
        "penalty": None,
        "incident_score": 0.0,
        "penalty_score": 0.0,
    },
]


class PenaltyScoresTests(unittest.TestCase):
    def test_get_score_for_penalty_type(self):
        self.assertEqual(get_score_for_penalty_type("time_penalty"), 6.0)
        self.assertEqual(get_score_for_penalty_type("drive_through"), 8.0)
        self.assertEqual(get_score_for_penalty_type("stop_and_go"), 10.0)
        self.assertEqual(get_score_for_penalty_type("dsq"), 35.0)

    def test_unknown_penalty_type_uses_default(self):
        self.assertEqual(get_score_for_penalty_type("unknown"), DEFAULT_PENALTY_SCORE)
        self.assertEqual(get_score_for_penalty_type(""), DEFAULT_PENALTY_SCORE)

    def test_penalty_type_scores_match_table(self):
        for row in SITUATION_TABLE:
            penalty = row.get("penalty")
            expected_penalty_score = row["penalty_score"]
            if penalty is None:
                self.assertEqual(expected_penalty_score, 0.0, msg=row["situation"])
            else:
                self.assertEqual(
                    get_score_for_penalty_type(penalty),
                    expected_penalty_score,
                    msg=row["situation"],
                )

    def test_situation_table_penalty_codes_in_scores(self):
        for row in SITUATION_TABLE:
            penalty = row.get("penalty")
            if penalty is not None:
                self.assertIn(
                    penalty,
                    PENALTY_TYPE_SCORES,
                    msg=f"{row['situation']}: penalty {penalty} must be in PENALTY_TYPE_SCORES",
                )

    def test_situation_table_has_expected_rows(self):
        self.assertEqual(len(SITUATION_TABLE), 8)
        situations = {r["situation"] for r in SITUATION_TABLE}
        self.assertIn("Лёгкий боковой контакт", situations)
        self.assertIn("Netcode / racing incident", situations)

    def test_situation_table_incident_scores_non_negative(self):
        for row in SITUATION_TABLE:
            self.assertGreaterEqual(row["incident_score"], 0.0, msg=row["situation"])
            self.assertGreaterEqual(row["penalty_score"], 0.0, msg=row["situation"])


if __name__ == "__main__":
    unittest.main()
