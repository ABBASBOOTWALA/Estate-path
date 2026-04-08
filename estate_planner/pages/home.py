"""
Home / Dashboard page.
"""
import streamlit as st
from datetime import date
from agents.progress_agent import get_dashboard_data
from agents.checklist_agent import get_progress_summary
from core.storage import load_profile, update_task_status


def _status_color(days: int) -> str:
    if days < 0:
        return "🔴"
    if days <= 7:
        return "🟠"
    if days <= 30:
        return "🟡"
    return "🟢"


def _priority_badge(priority: str) -> str:
    return {"urgent": "🚨 Urgent", "high": "🔺 High", "medium": "🔹 Medium", "low": "⚪ Low"}.get(priority, priority)


def show():
    profile = load_profile()
    if not profile:
        st.info("Welcome to EstatePath. Please complete the **Intake** to get started.")
        st.page_link("app.py", label="Go to Intake →")
        return

    st.header(f"Estate of {profile.full_name}")
    st.caption(f"Executor: {profile.executor_name}  |  Date of Death: {profile.date_of_death}  |  State: {profile.state_of_residence}")
    st.divider()

    # ── Stats ───────────────────────────────────────────────────────────────
    with st.spinner("Loading dashboard..."):
        data = get_dashboard_data()
    summary = data["summary"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tasks Completed", f"{summary['completed']} / {summary['total']}", f"{summary['pct_complete']}%")
    col2.metric("Overdue", summary["overdue"], delta=None, delta_color="inverse" if summary["overdue"] > 0 else "normal")
    col3.metric("Due in 30 Days", summary["urgent_due_soon"])
    col4.metric("Blocked", summary["blocked"])

    st.divider()

    # ── Progress by category ────────────────────────────────────────────────
    st.subheader("Progress by Category")
    cat_icons = {
        "government": "🏛️", "financial": "💰", "insurance": "🛡️",
        "legal": "⚖️", "property": "🏠", "digital": "💻",
        "tax": "📋", "medical": "🏥"
    }
    by_cat = summary.get("by_category", {})
    cat_cols = st.columns(4)
    for idx, (cat, counts) in enumerate(sorted(by_cat.items())):
        pct = round(counts["completed"] / counts["total"] * 100) if counts["total"] else 0
        icon = cat_icons.get(cat, "📌")
        with cat_cols[idx % 4]:
            st.metric(
                f"{icon} {cat.title()}",
                f"{counts['completed']}/{counts['total']}",
                f"{pct}%"
            )

    st.divider()

    # ── Two columns: Next Steps + Upcoming Deadlines ────────────────────────
    left, right = st.columns([1, 1])

    with left:
        st.subheader("Recommended Next Steps")
        next_tasks = data["next_tasks"]
        if not next_tasks:
            st.success("All tasks are complete or in progress. Great work!")
        for task in next_tasks:
            with st.container(border=True):
                badge = _priority_badge(task.priority)
                st.markdown(f"**{task.title}** — {badge}")
                st.caption(f"{task.institution}")
                if task.deadline:
                    days_left = (date.fromisoformat(task.deadline) - date.today()).days
                    st.caption(f"Deadline: {task.deadline} ({days_left} days)")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("Start", key=f"start_{task.task_id}", use_container_width=True):
                        update_task_status(task.task_id, "in_progress")
                        st.rerun()
                with c2:
                    if st.button("Done ✓", key=f"done_{task.task_id}", use_container_width=True):
                        update_task_status(task.task_id, "completed")
                        st.rerun()
                with c3:
                    if st.button("Skip", key=f"skip_{task.task_id}", use_container_width=True):
                        update_task_status(task.task_id, "skipped")
                        st.rerun()

    with right:
        st.subheader("Upcoming Deadlines")
        deadlines = data["urgent_deadlines"]
        if not deadlines:
            st.info("No deadlines in the next 30 days.")
        for d in deadlines:
            icon = _status_color(d.days_remaining)
            with st.container(border=True):
                st.markdown(f"{icon} **{d.title}**")
                label = f"Overdue by {abs(d.days_remaining)} days" if d.days_remaining < 0 else f"Due in {d.days_remaining} days"
                st.caption(f"{d.due_date} — {label}")
                if d.legal_basis:
                    st.caption(f"📜 {d.legal_basis}")

    st.divider()

    # ── Recent Activity ──────────────────────────────────────────────────────
    st.subheader("Recent Activity")
    activity = data["recent_activity"]
    if not activity:
        st.caption("No activity yet.")
    for entry in activity:
        ts = entry.timestamp[:10] if entry.timestamp else ""
        st.caption(f"`{ts}` — {entry.description}")
