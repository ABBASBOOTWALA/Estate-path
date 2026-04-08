"""
Progress Agent — generates dashboard summaries and status narratives.
"""
from core.storage import load_tasks, load_activity_log, load_profile
from core.claude_client import ask_claude
from agents.checklist_agent import get_progress_summary, get_next_recommended
from agents.deadline_agent import get_urgent_deadlines


def generate_narrative() -> str:
    """Use Claude to generate a plain-English status summary."""
    summary = get_progress_summary()
    profile = load_profile()
    name = profile.full_name if profile else "the estate"
    next_tasks = get_next_recommended(3)
    urgent = get_urgent_deadlines(30)

    next_str = "\n".join(f"- {t.title} ({t.priority} priority)" for t in next_tasks) or "None"
    urgent_str = "\n".join(f"- {d.title}: due {d.due_date} ({d.days_remaining} days)" for d in urgent[:5]) or "None"

    system = (
        "You are EstatePath, a compassionate estate settlement assistant. "
        "Write a brief, warm, plain-English summary of where the estate stands. "
        "Acknowledge that this is a hard process. Be encouraging but honest. "
        "Keep it under 120 words. No bullet points — write in 2–3 short paragraphs."
    )
    user = (
        f"Estate: {name}\n"
        f"Progress: {summary['completed']} of {summary['total']} tasks completed ({summary['pct_complete']}%)\n"
        f"Overdue: {summary['overdue']} tasks\n"
        f"Upcoming deadlines (30 days): {summary['urgent_due_soon']}\n"
        f"Blocked: {summary['blocked']}\n\n"
        f"Next recommended tasks:\n{next_str}\n\n"
        f"Urgent deadlines:\n{urgent_str}\n\n"
        "Write the status summary."
    )
    return ask_claude(system, user)


def get_dashboard_data() -> dict:
    """Return all data needed to render the home dashboard."""
    summary = get_progress_summary()
    next_tasks = get_next_recommended(3)
    urgent_deadlines = get_urgent_deadlines(30)
    activity = load_activity_log()[:5]

    return {
        "summary": summary,
        "next_tasks": next_tasks,
        "urgent_deadlines": sorted(urgent_deadlines, key=lambda d: d.due_date)[:8],
        "recent_activity": activity,
    }
