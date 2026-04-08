"""
Timeline / Deadline Calendar page.
"""
import streamlit as st
from datetime import date
from core.storage import load_profile
from agents.deadline_agent import refresh_days_remaining, calculate_deadlines, load_deadlines
from core.storage import load_deadlines as storage_load_deadlines


def _urgency_label(days: int) -> tuple[str, str]:
    if days < 0:
        return "🔴 OVERDUE", "red"
    if days == 0:
        return "🔴 DUE TODAY", "red"
    if days <= 7:
        return "🟠 This week", "orange"
    if days <= 30:
        return "🟡 This month", "goldenrod"
    return "🟢 Upcoming", "green"


def show():
    profile = load_profile()
    if not profile:
        st.info("Please complete the **Intake** first.")
        return

    st.header("Deadline Timeline")
    st.caption(f"Legal and recommended deadlines for the estate of {profile.full_name} in {profile.state_of_residence}")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Recalculate Deadlines", type="secondary"):
            with st.spinner("Recalculating..."):
                calculate_deadlines(profile)
            st.success("Deadlines updated.")
            st.rerun()

    deadlines = refresh_days_remaining()
    if not deadlines:
        st.info("No deadlines found. Click 'Recalculate Deadlines' to generate them.")
        return

    # ── Filter ────────────────────────────────────────────────────────────
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        show_only = st.radio(
            "Show",
            ["All", "Overdue", "Next 30 days", "Hard deadlines only"],
            horizontal=True,
        )
    with filter_col2:
        hide_far = st.checkbox("Hide deadlines more than 1 year away", value=True)

    today = date.today()
    filtered = deadlines
    if show_only == "Overdue":
        filtered = [d for d in deadlines if d.days_remaining < 0]
    elif show_only == "Next 30 days":
        filtered = [d for d in deadlines if 0 <= d.days_remaining <= 30]
    elif show_only == "Hard deadlines only":
        filtered = [d for d in deadlines if d.is_hard_deadline]

    if hide_far:
        filtered = [d for d in filtered if d.days_remaining <= 365]

    filtered.sort(key=lambda d: d.due_date)

    if not filtered:
        st.info("No deadlines match your filter.")
        return

    # ── Overdue banner ────────────────────────────────────────────────────
    overdue = [d for d in filtered if d.days_remaining < 0]
    if overdue:
        st.error(f"⚠️ {len(overdue)} overdue deadline(s) require immediate attention.")

    st.divider()

    # ── Deadline Cards ────────────────────────────────────────────────────
    for d in filtered:
        label, color = _urgency_label(d.days_remaining)
        hard_badge = "⚖️ Legal deadline" if d.is_hard_deadline else "📌 Recommended"

        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{d.title}**")
                st.caption(f"{hard_badge}  |  {d.legal_basis}")
            with col2:
                st.markdown(f"**Due:** {d.due_date}")
                st.markdown(f":{color}[{label}]" if color in ("red","orange","green","goldenrod") else label)
            with col3:
                days_text = f"Overdue by {abs(d.days_remaining)}d" if d.days_remaining < 0 else f"{d.days_remaining} days left"
                st.metric("", days_text)

            with st.expander("Why this matters"):
                st.write(d.consequences_if_missed)

    st.divider()

    # ── Add Custom Deadline ───────────────────────────────────────────────
    with st.expander("Add a Custom Deadline"):
        st.caption("Add attorney-specified deadlines or custom reminders.")
        from core.models import Deadline
        import uuid
        from core.storage import save_deadlines

        c1, c2 = st.columns(2)
        with c1:
            custom_title = st.text_input("Deadline title", key="custom_title")
            custom_date = st.date_input("Due date", key="custom_date", format="YYYY-MM-DD")
        with c2:
            custom_legal = st.text_input("Legal basis (optional)", key="custom_legal")
            custom_consequence = st.text_area("Consequences if missed (optional)", key="custom_consequence", height=80)
        custom_hard = st.checkbox("This is a hard legal deadline", key="custom_hard")

        if st.button("Add Deadline", type="primary"):
            if custom_title and custom_date:
                all_deadlines = storage_load_deadlines()
                new_deadline = Deadline(
                    deadline_id=f"custom-{str(uuid.uuid4())[:6]}",
                    task_id="custom",
                    title=custom_title,
                    due_date=custom_date.isoformat(),
                    days_remaining=(custom_date - today).days,
                    legal_basis=custom_legal,
                    consequences_if_missed=custom_consequence,
                    is_hard_deadline=custom_hard,
                )
                all_deadlines.append(new_deadline)
                save_deadlines(all_deadlines)
                st.success(f"Custom deadline '{custom_title}' added.")
                st.rerun()
            else:
                st.error("Please enter a title and due date.")
