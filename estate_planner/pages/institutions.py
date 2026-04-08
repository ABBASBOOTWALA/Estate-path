"""
Institutions page — institution-specific guidance and contact tracker.
"""
import json
import streamlit as st
from pathlib import Path
from core.storage import load_profile

_INSTITUTIONS_PATH = Path(__file__).parent.parent / "data" / "institutions.json"

CAT_ICONS = {
    "government": "🏛️", "financial": "💰", "insurance": "🛡️",
    "legal": "⚖️", "property": "🏠", "digital": "💻",
    "tax": "📋", "medical": "🏥"
}


def _load_institutions() -> list:
    with open(_INSTITUTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def show():
    profile = load_profile()
    st.header("Institution Guide")
    st.caption("Step-by-step guidance for notifying each institution and what they require.")

    institutions = _load_institutions()

    # ── Filters ────────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Search institutions", placeholder="e.g. bank, SSA, insurance...", key="inst_search")
    with col2:
        all_cats = ["All"] + sorted({i["category"] for i in institutions})
        cat_filter = st.selectbox("Category", all_cats, key="inst_cat")

    filtered = institutions
    if cat_filter != "All":
        filtered = [i for i in filtered if i["category"] == cat_filter]
    if search:
        q = search.lower()
        filtered = [i for i in filtered if q in i["name"].lower() or q in i.get("process_summary", "").lower()]

    st.caption(f"Showing {len(filtered)} institution(s)")
    st.divider()

    if not filtered:
        st.info("No institutions match your search.")

    for inst in filtered:
        icon = CAT_ICONS.get(inst["category"], "📌")
        with st.expander(f"{icon} {inst['name']}", expanded=False):
            # Header info
            col1, col2, col3 = st.columns(3)
            with col1:
                if inst.get("phone"):
                    st.markdown(f"📞 **{inst['phone']}**")
                else:
                    st.caption("No central phone number")
            with col2:
                if inst.get("online_portal"):
                    st.markdown(f"🌐 [{inst['online_portal']}](https://{inst['online_portal']})")
            with col3:
                if inst.get("typical_timeline"):
                    st.caption(f"⏱️ {inst['typical_timeline']}")

            st.markdown("**How to notify them:**")
            st.write(inst.get("process_summary", ""))

            if inst.get("required_documents"):
                st.markdown("**Documents they'll need:**")
                for doc in inst["required_documents"]:
                    st.markdown(f"  - {doc}")

            if inst.get("mail_address"):
                st.caption(f"📬 {inst['mail_address']}")

            if inst.get("important_notes"):
                st.warning(f"⚠️ **Important:** {inst['important_notes']}")

    st.divider()

    # ── Add Custom Institution ────────────────────────────────────────────
    with st.expander("Add a Custom Institution"):
        st.caption("Add any institution not listed above — local bank branch, specialty insurer, etc.")

        if "custom_institutions" not in st.session_state:
            st.session_state.custom_institutions = []

        c1, c2 = st.columns(2)
        with c1:
            ci_name = st.text_input("Institution name", key="ci_name")
            ci_phone = st.text_input("Phone", key="ci_phone")
            ci_contact = st.text_input("Contact person name (optional)", key="ci_contact")
        with c2:
            ci_cat = st.selectbox("Category", list(CAT_ICONS.keys()), key="ci_cat")
            ci_account = st.text_input("Account / policy number", key="ci_account")
            ci_url = st.text_input("Website / portal", key="ci_url")

        ci_notes = st.text_area("Notes", key="ci_notes", height=80)

        if st.button("Save Custom Institution", type="primary"):
            if ci_name:
                st.session_state.custom_institutions.append({
                    "name": ci_name, "category": ci_cat, "phone": ci_phone,
                    "contact": ci_contact, "account": ci_account,
                    "url": ci_url, "notes": ci_notes
                })
                st.success(f"'{ci_name}' saved to your custom institutions.")
                st.rerun()

        if st.session_state.custom_institutions:
            st.subheader("Your Custom Institutions")
            for ci in st.session_state.custom_institutions:
                icon = CAT_ICONS.get(ci["category"], "📌")
                with st.container(border=True):
                    st.markdown(f"{icon} **{ci['name']}** — {ci['category'].title()}")
                    if ci["phone"]:
                        st.caption(f"📞 {ci['phone']}")
                    if ci["account"]:
                        st.caption(f"Account: {ci['account']}")
                    if ci["notes"]:
                        st.caption(ci["notes"])
