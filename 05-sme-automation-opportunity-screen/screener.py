"""Small, deterministic decision-support screener for synthetic SME automation use cases.

Not a financial valuation, AI model, implementation authorization or measurement of ROI.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

MONEY = Decimal("0.01")
ONE_DECIMAL = Decimal("0.1")
FIELDS = (
    "opportunity_id", "company", "process", "cases_per_month",
    "manual_minutes", "automated_minutes", "automatable_share",
    "loaded_hourly_cost_eur", "setup_cost_eur", "monthly_running_cost_eur",
    "data_classification", "systems_access_confirmed", "process_owner_approved",
)


@dataclass(frozen=True)
class ScreeningResult:
    opportunity_id: str
    company: str
    process: str
    hours_saved_per_month: str
    gross_savings_per_month_eur: str
    net_savings_per_month_eur: str
    first_year_net_after_setup_eur: str
    simple_payback_months: str | None
    disposition: str
    review_reasons: list[str]


def decimal_field(row: dict[str, str], name: str, minimum: Decimal = Decimal("0")) -> Decimal:
    try:
        value = Decimal(row[name].strip())
    except (KeyError, AttributeError, InvalidOperation) as exc:
        raise ValueError(f"{name} must be a decimal number") from exc
    if not value.is_finite() or value < minimum:
        raise ValueError(f"{name} must be finite and >= {minimum}")
    return value


def yes_no(row: dict[str, str], name: str) -> bool:
    raw = row[name].strip().lower()
    if raw not in {"yes", "no"}:
        raise ValueError(f"{name} must be yes or no")
    return raw == "yes"


def money(value: Decimal) -> str:
    return str(value.quantize(MONEY, rounding=ROUND_HALF_UP))


def screen(row: dict[str, str]) -> ScreeningResult:
    """Estimate hypothetical value; never auto-approve an implementation."""
    if any(not row.get(name, "").strip() for name in ("opportunity_id", "company", "process")):
        raise ValueError("opportunity_id, company and process must be nonempty")

    cases = decimal_field(row, "cases_per_month")
    if cases != cases.to_integral_value():
        raise ValueError("cases_per_month must be a whole number")
    manual_minutes = decimal_field(row, "manual_minutes")
    automated_minutes = decimal_field(row, "automated_minutes")
    share = decimal_field(row, "automatable_share")
    if share > Decimal("1"):
        raise ValueError("automatable_share must be between 0 and 1")
    hourly = decimal_field(row, "loaded_hourly_cost_eur")
    setup = decimal_field(row, "setup_cost_eur")
    running = decimal_field(row, "monthly_running_cost_eur")
    classification = row["data_classification"].strip().lower()
    if classification not in {"low", "medium", "high"}:
        raise ValueError("data_classification must be low, medium or high")
    access = yes_no(row, "systems_access_confirmed")
    owner = yes_no(row, "process_owner_approved")

    saved_minutes = cases * share * max(manual_minutes - automated_minutes, Decimal("0"))
    saved_hours = saved_minutes / Decimal("60")
    gross_monthly = saved_hours * hourly
    net_monthly = gross_monthly - running
    first_year = net_monthly * Decimal("12") - setup
    payback = setup / net_monthly if net_monthly > 0 else None

    review_reasons: list[str] = []
    if classification == "high":
        review_reasons.append("high-data-sensitivity: privacy/security assessment required")
    if not access:
        review_reasons.append("system-access feasibility not confirmed")
    if not owner:
        review_reasons.append("process owner has not approved discovery")

    if review_reasons:
        disposition = "needs_human_review"
    elif net_monthly <= 0 or first_year <= 0:
        disposition = "weak_economics"
    else:
        disposition = "candidate_for_discovery"

    return ScreeningResult(
        opportunity_id=row["opportunity_id"].strip(),
        company=row["company"].strip(),
        process=row["process"].strip(),
        hours_saved_per_month=str(saved_hours.quantize(ONE_DECIMAL, rounding=ROUND_HALF_UP)),
        gross_savings_per_month_eur=money(gross_monthly),
        net_savings_per_month_eur=money(net_monthly),
        first_year_net_after_setup_eur=money(first_year),
        simple_payback_months=(str(payback.quantize(ONE_DECIMAL, rounding=ROUND_HALF_UP)) if payback is not None else None),
        disposition=disposition,
        review_reasons=review_reasons,
    )


def load(path: Path) -> list[ScreeningResult]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("input CSV needs a header")
        missing = sorted(set(FIELDS).difference(reader.fieldnames))
        if missing:
            raise ValueError("missing CSV columns: " + ", ".join(missing))
        seen: set[str] = set()
        results = []
        for line, row in enumerate(reader, 2):
            try:
                result = screen(row)
            except (KeyError, ValueError, AttributeError) as exc:
                raise ValueError(f"CSV line {line}: {exc}") from exc
            if result.opportunity_id in seen:
                raise ValueError(f"CSV line {line}: duplicate opportunity_id")
            seen.add(result.opportunity_id)
            results.append(result)
    if not results:
        raise ValueError("input CSV must contain at least one opportunity")
    priority = {"candidate_for_discovery": 0, "needs_human_review": 1, "weak_economics": 2}
    return sorted(results, key=lambda x: (priority[x.disposition], -Decimal(x.net_savings_per_month_eur), x.opportunity_id))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV of synthetic opportunity assumptions")
    args = parser.parse_args()
    try:
        results = load(args.input)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "disclaimer": "Hypothetical assumptions, not verified ROI. Manual approval required for every pilot.",
        "opportunities": [asdict(row) for row in results],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
