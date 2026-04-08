"""
Checklist Agent — generates and manages the estate task list.
"""
import json
from pathlib import Path
from typing import List

from core.models import EstateTask, DeceasedProfile
from core.storage import load_tasks, save_tasks, load_profile
from core.claude_client import ask_claude
from dateutil.relativedelta import relativedelta
from datetime import date


_TASK_LIBRARY_PATH = Path(__file__).parent.parent / "data" / "task_library.json"


def _load_library() -> List[dict]:
    with open(_TASK_LIBRARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _calculate_deadline(rule: str, dod: str) -> str | None:
    """Convert a deadline rule into an ISO date given date of death."""
    try:
        death = date.fromisoformat(dod)
    except Exception:
        return None

    rule_lower = rule.lower()
    if "first week" in rule_lower:
        return (death + relativedelta(weeks=1)).isoformat()
    if "two weeks" in rule_lower:
        return (death + relativedelta(weeks=2)).isoformat()
    if "30 days" in rule_lower or "within 30" in rule_lower:
        return (death + relativedelta(days=30)).isoformat()
    if "60 days" in rule_lower:
        return (death + relativedelta(days=60)).isoformat()
    if "90 days" in rule_lower:
        return (death + relativedelta(days=90)).isoformat()
    if "6 months" in rule_lower:
        return (death + relativedelta(months=6)).isoformat()
    if "9 months" in rule_lower:
        return (death + relativedelta(months=9)).isoformat()
    if "april 15" in rule_lower or "following year" in rule_lower:
        return date(death.year + 1, 4, 15).isoformat()
    return None


def _task_applies(task: dict, profile: DeceasedProfile) -> bool:
    """Filter tasks based on the estate profile."""
    tid = task["task_id"]

    # VA tasks only if veteran
    if tid.startswith("va-") and not profile.is_veteran:
        return False

    # Trust administration only if has trust
    if tid == "trust-administration" and not profile.has_trust:
        return False

    # Real estate only if has property
    if tid == "real-estate-title-transfer" and not profile.has_real_property:
        return False

    # Mortgage only if has property
    if tid == "mortgage-notification" and not profile.has_real_property:
        return False

    # Vehicle title only if has vehicles
    if tid == "vehicle-title-transfer" and not profile.vehicles:
        return False

    # Auto loan only if has vehicles
    if tid == "auto-loan-notification" and not profile.vehicles:
        return False

    # Business interests
    if tid == "trust-administration" and not profile.has_business_interests:
        pass  # already handled above

    # Estate tax return only if large estate
    large_estate_values = ["$500k–$1M", "$1M–$5M", "$5M+"]
    if tid == "estate-tax-return" and profile.estimated_estate_value not in large_estate_values:
        return False

    return True


def generate_task_list(profile: DeceasedProfile) -> List[EstateTask]:
    """Generate a personalized task list from the library based on the profile."""
    library = _load_library()
    tasks = []
    for item in library:
        if not _task_applies(item, profile):
            continue
        task = EstateTask(
            task_id=item["task_id"],
            category=item["category"],
            title=item["title"],
            institution=item["institution"],
            description=item["description"],
            status="not_started",
            priority=item.get("priority", "medium"),
            deadline_rule=item.get("deadline_rule", ""),
            documents_needed=item.get("documents_needed", []),
            can_auto_generate=item.get("can_auto_generate", False),
            template_name=item.get("template_name"),
            contact_phone=item.get("contact_phone", ""),
            contact_url=item.get("contact_url", ""),
            deadline=_calculate_deadline(item.get("deadline_rule", ""), profile.date_of_death),
        )
        tasks.append(task)
    save_tasks(tasks)
    return tasks


def get_next_recommended(n: int = 3) -> List[EstateTask]:
    """Return the top N tasks to work on next."""
    tasks = load_tasks()
    active = [t for t in tasks if t.status in ("not_started", "in_progress", "blocked")]

    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    active.sort(key=lambda t: (priority_order.get(t.priority, 9), t.deadline or "9999"))
    return active[:n]


def explain_task(task_id: str) -> str:
    """Use Claude to explain why a task matters and what to do."""
    tasks = load_tasks()
    task = next((t for t in tasks if t.task_id == task_id), None)
    if not task:
        return "Task not found."

    profile = load_profile()
    name = profile.full_name if profile else "the deceased"

    system = (
        "You are EstatePath, a compassionate estate settlement assistant. "
        "Explain estate tasks clearly and kindly. The user is grieving and may be unfamiliar with legal processes. "
        "Keep your response under 150 words. Be warm, practical, and avoid legal jargon."
    )
    user = (
        f"Explain this estate task and why it matters:\n"
        f"Task: {task.title}\n"
        f"Institution: {task.institution}\n"
        f"Description: {task.description}\n"
        f"Priority: {task.priority}\n"
        f"Deadline rule: {task.deadline_rule}\n"
        f"This is for the estate of {name}."
    )
    return ask_claude(system, user)


def get_progress_summary() -> dict:
    """Return counts by status and category."""
    tasks = load_tasks()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "completed")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    blocked = sum(1 for t in tasks if t.status == "blocked")
    not_started = sum(1 for t in tasks if t.status == "not_started")

    today = date.today().isoformat()
    overdue = sum(1 for t in tasks if t.deadline and t.deadline < today and t.status != "completed")
    urgent_due_soon = sum(
        1 for t in tasks
        if t.deadline and today <= t.deadline <= (date.today() + relativedelta(days=30)).isoformat()
        and t.status != "completed"
    )

    by_category = {}
    for t in tasks:
        cat = t.category
        if cat not in by_category:
            by_category[cat] = {"total": 0, "completed": 0}
        by_category[cat]["total"] += 1
        if t.status == "completed":
            by_category[cat]["completed"] += 1

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "blocked": blocked,
        "not_started": not_started,
        "overdue": overdue,
        "urgent_due_soon": urgent_due_soon,
        "by_category": by_category,
        "pct_complete": round(completed / total * 100, 1) if total else 0,
    }
