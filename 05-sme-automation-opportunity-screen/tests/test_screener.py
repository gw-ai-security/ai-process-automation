import csv
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from screener import load, screen

HEADER = [
    "opportunity_id", "company", "process", "cases_per_month", "manual_minutes",
    "automated_minutes", "automatable_share", "loaded_hourly_cost_eur",
    "setup_cost_eur", "monthly_running_cost_eur", "data_classification",
    "systems_access_confirmed", "process_owner_approved",
]
BASE = {
    "opportunity_id": "demo-1", "company": "Fictional Co", "process": "Manual matching",
    "cases_per_month": "100", "manual_minutes": "10", "automated_minutes": "4",
    "automatable_share": "0.5", "loaded_hourly_cost_eur": "30",
    "setup_cost_eur": "100", "monthly_running_cost_eur": "5",
    "data_classification": "low", "systems_access_confirmed": "yes",
    "process_owner_approved": "yes",
}


class ScreeningTests(unittest.TestCase):
    def test_value_formula_and_payback(self):
        outcome = screen(BASE)
        self.assertEqual(outcome.hours_saved_per_month, "5.0")
        self.assertEqual(outcome.gross_savings_per_month_eur, "150.00")
        self.assertEqual(outcome.net_savings_per_month_eur, "145.00")
        self.assertEqual(outcome.first_year_net_after_setup_eur, "1640.00")
        self.assertEqual(outcome.simple_payback_months, "0.7")
        self.assertEqual(outcome.disposition, "candidate_for_discovery")

    def test_sensitive_data_always_requires_review(self):
        outcome = screen({**BASE, "data_classification": "high"})
        self.assertEqual(outcome.disposition, "needs_human_review")
        self.assertTrue(outcome.review_reasons)

    def test_unapproved_owner_blocks_candidate(self):
        self.assertEqual(screen({**BASE, "process_owner_approved": "no"}).disposition, "needs_human_review")

    def test_access_not_verified_blocks_candidate(self):
        self.assertEqual(screen({**BASE, "systems_access_confirmed": "no"}).disposition, "needs_human_review")

    def test_weak_economics_and_no_payback(self):
        outcome = screen({**BASE, "monthly_running_cost_eur": "400"})
        self.assertEqual(outcome.disposition, "weak_economics")
        self.assertIsNone(outcome.simple_payback_months)

    def test_automated_slower_than_manual_never_yields_savings(self):
        outcome = screen({**BASE, "automated_minutes": "20"})
        self.assertEqual(outcome.hours_saved_per_month, "0.0")

    def test_reject_nonfinite_negative_and_invalid_share(self):
        for field, value in [("manual_minutes", "NaN"), ("setup_cost_eur", "-1"),
                             ("automatable_share", "1.2"), ("cases_per_month", "10.5")]:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    screen({**BASE, field: value})

    def test_reject_duplicate_ids_and_sort(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidates.csv"
            def write(rows):
                with path.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=HEADER)
                    writer.writeheader()
                    writer.writerows(rows)
            write([BASE, {**BASE, "opportunity_id": "demo-2", "data_classification": "high"}])
            self.assertEqual([r.opportunity_id for r in load(path)], ["demo-1", "demo-2"])
            write([BASE, BASE])
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load(path)

    def test_no_unintended_nonfinite_calculation(self):
        result = screen({**BASE, "automatable_share": "0"})
        self.assertEqual(Decimal(result.net_savings_per_month_eur), Decimal("-5"))


if __name__ == "__main__":
    unittest.main()
