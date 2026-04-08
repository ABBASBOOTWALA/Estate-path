"""
Deadline Agent — calculates and tracks legal deadlines.
"""
import json
from pathlib import Path
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import List

from core.models import Deadline, DeceasedProfile
from core.storage import load_deadlines, save_deadlines, load_profile

_JURISDICTIONS_PATH = Path(__file__).parent.parent / "data" / "jurisdictions.json"


def _load_jurisdiction(state: str) -> dict:
    with open(_JURISDICTIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(state.upper(), {})


def calculate_deadlines(profile: DeceasedProfile) -> List[Deadline]:
    """Calculate all legal deadlines from the date of death."""
    try:
        dod = date.fromisoformat(profile.date_of_death)
    except Exception:
        return []

    today = date.today()
    state_info = _load_jurisdiction(profile.state_of_residence)
    deadlines: List[Deadline] = []

    def add(deadline_id, task_id, title, due: date, legal_basis, consequence, hard=True):
        days_rem = (due - today).days
        deadlines.append(Deadline(
            deadline_id=deadline_id,
            task_id=task_id,
            title=title,
            due_date=due.isoformat(),
            days_remaining=days_rem,
            legal_basis=legal_basis,
            consequences_if_missed=consequence,
            is_hard_deadline=hard,
        ))

    # SSA notification — ASAP (set 30-day target)
    add(
        "ssa-notify", "ssa-death-notification",
        "Notify Social Security Administration",
        dod + relativedelta(days=30),
        "Social Security Act §205",
        "Overpayments received after death must be returned. Failure to notify may result in federal liability.",
        hard=True,
    )

    # Final income tax return
    final_tax_due = date(dod.year + 1, 4, 15)
    add(
        "final-tax", "final-income-tax-return",
        "File Final Federal Income Tax Return (Form 1040)",
        final_tax_due,
        "26 U.S.C. §6072",
        "Penalties and interest accrue on late filings. The IRS may assess additional taxes.",
        hard=True,
    )

    # Estate tax return (9 months from death)
    add(
        "estate-tax", "estate-tax-return",
        "File Estate Tax Return (Form 706) if Required",
        dod + relativedelta(months=9),
        "26 U.S.C. §6075(a)",
        "Automatic 6-month extension available but must be requested. Late filing penalties are 5% per month.",
        hard=True,
    )

    # Medicare notification (90 days)
    add(
        "medicare-notify", "medicare-termination",
        "Notify Medicare of Death",
        dod + relativedelta(days=90),
        "42 U.S.C. §1395",
        "Continued billing may create overpayments that must be refunded.",
        hard=False,
    )

    # Order death certificates (1 week — soft deadline)
    add(
        "death-certs", "death-certificates-order",
        "Order Certified Death Certificates",
        dod + relativedelta(weeks=1),
        "Practical requirement",
        "All other estate tasks are blocked until you have certified death certificates.",
        hard=False,
    )

    # Obtain EIN (2 weeks — soft deadline)
    add(
        "ein-deadline", "ein-for-estate",
        "Obtain EIN for the Estate",
        dod + relativedelta(weeks=2),
        "26 U.S.C. §6109",
        "Cannot open an estate bank account or file estate tax return without an EIN.",
        hard=False,
    )

    # State-specific: creditor claim deadline
    creditor_days = state_info.get("creditor_claim_deadline_days", 180)
    creditor_state = state_info.get("state", profile.state_of_residence)
    add(
        "creditor-claims", "creditor-notification",
        f"Creditor Claim Deadline ({creditor_state})",
        dod + relativedelta(days=creditor_days),
        f"{creditor_state} probate law — {state_info.get('legal_citations', [''])[0] if state_info.get('legal_citations') else 'state law'}",
        "Creditors who miss this deadline may have their claims permanently barred. Executor may be personally liable for distributing assets before this period expires.",
        hard=True,
    )

    # Will filing (30 days — many states)
    add(
        "will-filing", "will-filing",
        "File Will with Probate Court",
        dod + relativedelta(days=30),
        f"State probate law — most states require filing within 30 days",
        "Failure to file a known will may be considered a criminal offense in some states. Delays can complicate estate administration.",
        hard=True,
    )

    # Life insurance claim (60 days — recommended)
    add(
        "life-ins-claim", "life-insurance-claim",
        "File Life Insurance Claim",
        dod + relativedelta(days=60),
        "Policy terms — typical recommended filing window",
        "While most policies have no hard deadline, delays can complicate claims and some policies have contestability clauses.",
        hard=False,
    )

    # Survivor benefits (6 months for retroactivity)
    add(
        "ssa-survivor", "ssa-survivor-benefits",
        "Apply for SSA Survivor Benefits",
        dod + relativedelta(months=6),
        "Social Security Act — benefits not retroactive beyond 6 months",
        "Benefits cannot be paid retroactively beyond 6 months before the application date. Early application maximizes potential benefits.",
        hard=False,
    )

    # VA death notification (30 days)
    if profile.is_veteran:
        add(
            "va-notify", "va-death-notification",
            "Notify VA of Death",
            dod + relativedelta(days=30),
            "38 U.S.C. §5112",
            "VA benefits overpaid after death must be returned. Survivor benefits (DIC) require separate application.",
            hard=True,
        )
        add(
            "va-dic", "va-survivor-benefits",
            "Apply for VA DIC Benefits (within 1 year for retroactivity)",
            dod + relativedelta(years=1),
            "38 C.F.R. §3.400",
            "DIC claims filed within 1 year of death may be retroactive to the date of death.",
            hard=False,
        )

    # Sort by due date
    deadlines.sort(key=lambda d: d.due_date)
    save_deadlines(deadlines)
    return deadlines


def refresh_days_remaining():
    """Recalculate days remaining for all deadlines based on today."""
    deadlines = load_deadlines()
    today = date.today()
    for d in deadlines:
        try:
            d.days_remaining = (date.fromisoformat(d.due_date) - today).days
        except Exception:
            pass
    save_deadlines(deadlines)
    return deadlines


def get_urgent_deadlines(days: int = 30) -> List[Deadline]:
    """Return deadlines due within N days."""
    deadlines = refresh_days_remaining()
    return [d for d in deadlines if d.days_remaining <= days]
