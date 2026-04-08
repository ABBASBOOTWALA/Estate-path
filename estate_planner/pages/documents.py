"""
Documents page — letter generator and document library.
"""
import streamlit as st
from pathlib import Path
from core.storage import load_tasks, load_documents, load_profile
from agents.document_agent import generate_letter

TEMPLATE_LABELS = {
    "death_notification": "Death Notification Letter",
    "account_closure": "Account Closure Letter",
    "insurance_claim": "Insurance Claim Letter",
    "probate_creditor": "Notice to Creditor",
    "certified_copy_request": "Certified Death Certificate Request",
    "beneficiary_claim": "Beneficiary Claim Letter",
}


def show():
    profile = load_profile()
    if not profile:
        st.info("Please complete the **Intake** first.")
        return

    st.header("Document Generator")
    st.caption("Generate professional letters for institutions automatically pre-filled with your estate information.")

    # ── Generator ──────────────────────────────────────────────────────────
    with st.container(border=True):
        st.subheader("Generate a Letter")

        tasks = load_tasks()
        generatable = [t for t in tasks if t.can_auto_generate and t.template_name]

        col1, col2 = st.columns([2, 1])
        with col1:
            # Option A: pick from task list
            task_options = {f"{t.title} → {t.institution}": t for t in generatable}
            selected_label = st.selectbox(
                "Select a task to generate a letter for",
                options=["— Choose a task —"] + list(task_options.keys()),
            )

        with col2:
            # Option B: manual template
            manual_template = st.selectbox(
                "Or choose a template directly",
                options=["— Manual —"] + list(TEMPLATE_LABELS.keys()),
                format_func=lambda x: TEMPLATE_LABELS.get(x, x),
            )

        # Resolve template and task
        selected_task = task_options.get(selected_label)
        if selected_task:
            template_name = selected_task.template_name
            default_institution = selected_task.institution
            default_task_id = selected_task.task_id
        elif manual_template != "— Manual —":
            template_name = manual_template
            default_institution = ""
            default_task_id = manual_template
        else:
            template_name = None
            default_institution = ""
            default_task_id = ""

        if template_name:
            st.info(f"Template: **{TEMPLATE_LABELS.get(template_name, template_name)}**")

            col3, col4 = st.columns(2)
            with col3:
                institution = st.text_input("Institution name", value=default_institution)
                account_number = st.text_input("Account / Policy number (leave blank if unknown)")
            with col4:
                institution_address = st.text_area("Institution mailing address (optional)", height=80,
                    placeholder="123 Main St\nAnytown, CA 90210")

            st.caption("The letter will be pre-filled with your estate profile information. Review the PDF before sending.")

            if st.button("Generate Letter →", type="primary", disabled=not institution):
                with st.spinner("Generating letter PDF..."):
                    try:
                        doc = generate_letter(
                            template_name=template_name,
                            task_id=default_task_id,
                            institution=institution,
                            account_number=account_number,
                            institution_address=institution_address,
                        )
                        st.success(f"Letter generated: **{doc.title}**")
                        # Offer download
                        file_path = Path(doc.file_path)
                        if file_path.exists():
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label="⬇ Download PDF",
                                    data=f.read(),
                                    file_name=file_path.name,
                                    mime="application/pdf",
                                )
                    except Exception as e:
                        st.error(f"Error generating letter: {e}")

    st.divider()

    # ── Document Library ────────────────────────────────────────────────────
    st.subheader("Document Library")
    docs = load_documents()

    if not docs:
        st.caption("No documents generated yet. Use the generator above to create your first letter.")
        return

    # Sort newest first
    docs_sorted = sorted(docs, key=lambda d: d.created_at, reverse=True)

    for doc in docs_sorted:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{doc.title}**")
                st.caption(f"Created: {doc.created_at[:10]} | Template: {TEMPLATE_LABELS.get(doc.template_used, doc.template_used)}")
            with col2:
                file_path = Path(doc.file_path)
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="⬇ Download",
                            data=f.read(),
                            file_name=file_path.name,
                            mime="application/pdf",
                            key=f"dl_{doc.doc_id}",
                        )
                else:
                    st.caption("File not found")
            with col3:
                st.caption(f"Task: {doc.task_id}")
