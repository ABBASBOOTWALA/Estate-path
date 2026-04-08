"""
Checklist page — task list with filters and status updates.
"""
import streamlit as st
from datetime import date
from core.storage import load_tasks, update_task_status, log_activity, load_profile
from agents.checklist_agent import explain_task

CATEGORIES = ["All", "government", "financial", "insurance", "legal", "property", "digital", "tax", "medical"]
STATUSES = ["All", "not_started", "in_progress", "completed", "blocked", "skipped"]
PRIORITIES = ["All", "urgent", "high", "medium", "low"]

CAT_ICONS = {
    "government": "🏛️", "financial": "💰", "insurance": "🛡️",
    "legal": "⚖️", "property": "🏠", "digital": "💻",
    "tax": "📋", "medical": "🏥"
}

STATUS_COLORS = {
    "not_started": "⬜", "in_progress": "🔵", "completed": "✅",
    "blocked": "🔴", "skipped": "⏭️"
}

PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def show():
    profile = load_profile()
    if not profile:
        st.info("Please complete the **Intake** first to generate your task list.")
        return

    st.header("Estate Checklist")
    st.caption(f"Your personalized task list for the estate of {profile.full_name}")

    # ── Filters ────────────────────────────────────────────────────────────
    with st.expander("Filter Tasks", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            cat_filter = st.selectbox("Category", CATEGORIES, key="filter_cat")
        with col2:
            status_filter = st.selectbox("Status", STATUSES, key="filter_status")
        with col3:
            priority_filter = st.selectbox("Priority", PRIORITIES, key="filter_priority")
        with col4:
            search = st.text_input("Search", placeholder="Search tasks...", key="filter_search")

    tasks = load_tasks()

    # Apply filters
    filtered = tasks
    if cat_filter != "All":
        filtered = [t for t in filtered if t.category == cat_filter]
    if status_filter != "All":
        filtered = [t for t in filtered if t.status == status_filter]
    if priority_filter != "All":
        filtered = [t for t in filtered if t.priority == priority_filter]
    if search:
        q = search.lower()
        filtered = [t for t in filtered if q in t.title.lower() or q in t.institution.lower() or q in t.description.lower()]

    # Sort
    filtered.sort(key=lambda t: (PRIORITY_ORDER.get(t.priority, 9), t.deadline or "9999", t.title))

    # Stats row
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "completed")
    st.caption(f"Showing {len(filtered)} of {total} tasks — {done} completed ({round(done/total*100) if total else 0}%)")
    st.divider()

    if not filtered:
        st.info("No tasks match your filters.")
        return

    # ── Task Cards ─────────────────────────────────────────────────────────
    for task in filtered:
        icon = CAT_ICONS.get(task.category, "📌")
        status_icon = STATUS_COLORS.get(task.status, "⬜")

        with st.expander(f"{status_icon} {icon} **{task.title}** — {task.institution}", expanded=False):
            # Priority & deadline
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                priority_label = {"urgent": "🚨 Urgent", "high": "🔺 High", "medium": "🔹 Medium", "low": "⚪ Low"}.get(task.priority, task.priority)
                st.markdown(f"**Priority:** {priority_label}")
            with col2:
                if task.deadline:
                    days_left = (date.fromisoformat(task.deadline) - date.today()).days
                    color = "red" if days_left < 0 else ("orange" if days_left <= 7 else "inherit")
                    st.markdown(f"**Deadline:** :{color}[{task.deadline}] ({days_left}d)")
                else:
                    st.markdown("**Deadline:** No hard deadline")
            with col3:
                st.markdown(f"**Category:** {task.category.title()}")

            st.markdown(f"**What to do:** {task.description}")

            if task.deadline_rule:
                st.caption(f"⏰ {task.deadline_rule}")

            if task.documents_needed:
                st.markdown("**Documents needed:**")
                for doc in task.documents_needed:
                    st.markdown(f"  - {doc}")

            if task.contact_phone:
                st.caption(f"📞 {task.contact_phone}")
            if task.contact_url:
                st.caption(f"🌐 {task.contact_url}")

            # Notes
            notes_key = f"notes_{task.task_id}"
            new_notes = st.text_area("Notes", value=task.notes, key=notes_key, height=80, label_visibility="collapsed", placeholder="Add notes...")

            # Action buttons
            st.markdown("**Update status:**")
            bcols = st.columns(5)
            statuses = [
                ("Not Started", "not_started", "⬜"),
                ("In Progress", "in_progress", "🔵"),
                ("Completed", "completed", "✅"),
                ("Blocked", "blocked", "🔴"),
                ("Skipped", "skipped", "⏭️"),
            ]
            for idx, (label, status_val, ico) in enumerate(statuses):
                with bcols[idx]:
                    is_current = task.status == status_val
                    btn_type = "primary" if is_current else "secondary"
                    if st.button(f"{ico} {label}", key=f"status_{task.task_id}_{status_val}", type=btn_type, use_container_width=True):
                        notes = st.session_state.get(notes_key, task.notes)
                        update_task_status(task.task_id, status_val, notes)
                        log_activity(f"status_{status_val}", f"{task.title} marked as {status_val}", task.task_id)
                        st.rerun()

            # Explain task button
            if st.button(f"💡 Why does this matter?", key=f"explain_{task.task_id}"):
                with st.spinner("Getting guidance..."):
                    explanation = explain_task(task.task_id)
                st.info(explanation)
