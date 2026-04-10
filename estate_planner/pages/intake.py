"""
Intake page — multi-step wizard to collect estate profile.
"""
import streamlit as st
from datetime import date
from core.models import DeceasedProfile
from core.storage import save_profile, log_activity
from agents.checklist_agent import generate_task_list
from agents.deadline_agent import calculate_deadlines

US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH",
    "NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT",
    "VT","VA","WA","WV","WI","WY"
]

DIGITAL_PLATFORMS = [
    "Google / Gmail", "Apple / iCloud", "Facebook / Instagram", "Amazon",
    "PayPal / Venmo", "Netflix", "Spotify", "Hulu / Disney+",
    "Microsoft / Outlook", "Twitter / X", "LinkedIn", "Dropbox",
    "Cryptocurrency wallet", "Other"
]

ESTATE_VALUES = [
    "Under $25,000", "$25k–$100k", "$100k–$500k",
    "$500k–$1M", "$1M–$5M", "$5M+"
]


def show():
    st.header("Estate Intake")
    st.caption("Complete this once to personalize your estate checklist, deadlines, and guidance.")
    st.info(
        "**Your data is encrypted.** All personal information (name, SSN, addresses) is encrypted "
        "using AES-256 (Fernet) and the encryption key is stored in your OS keychain "
        "(Windows Credential Manager). Nothing is uploaded or transmitted.",
        icon="🔒",
    )

    if "intake_step" not in st.session_state:
        st.session_state.intake_step = 1
    if "intake_data" not in st.session_state:
        st.session_state.intake_data = {}

    step = st.session_state.intake_step
    total_steps = 7

    # Progress bar
    st.progress(step / total_steps, text=f"Step {step} of {total_steps}")
    st.divider()

    data = st.session_state.intake_data

    # ── Step 1: Deceased Info ──────────────────────────────────────────────
    if step == 1:
        st.subheader("About the Deceased")
        st.caption("We're sorry for your loss. This information helps us personalize your checklist.")

        data["full_name"] = st.text_input("Full legal name", value=data.get("full_name", ""))
        col1, col2 = st.columns(2)
        with col1:
            data["date_of_birth"] = st.date_input(
                "Date of birth",
                value=date(1945, 1, 1),
                min_value=date(1880, 1, 1),
                max_value=date.today(),
                format="YYYY-MM-DD", key="dob"
            )
        with col2:
            data["date_of_death"] = st.date_input(
                "Date of death",
                value=date.today(),
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                format="YYYY-MM-DD", key="dod"
            )

        col3, col4 = st.columns(2)
        with col3:
            data["state_of_residence"] = st.selectbox(
                "State of residence at time of death",
                options=US_STATES,
                index=US_STATES.index(data.get("state_of_residence", "CA")) if data.get("state_of_residence") in US_STATES else 4,
            )
        with col4:
            data["county"] = st.text_input("County", value=data.get("county", ""))

        data["is_veteran"] = st.checkbox("Was the deceased a U.S. military veteran?", value=data.get("is_veteran", False))

        if st.button("Next →", type="primary"):
            if not data.get("full_name") or not data.get("date_of_death"):
                st.error("Please fill in the full name and date of death.")
            else:
                if hasattr(data["date_of_birth"], "isoformat"):
                    data["date_of_birth"] = data["date_of_birth"].isoformat()
                if hasattr(data["date_of_death"], "isoformat"):
                    data["date_of_death"] = data["date_of_death"].isoformat()
                st.session_state.intake_step = 2
                st.rerun()

    # ── Step 2: Estate Basics ──────────────────────────────────────────────
    elif step == 2:
        st.subheader("About the Estate")

        data["had_will"] = st.radio(
            "Did the deceased have a will?",
            ["Yes", "No", "Unknown"],
            index=["Yes","No","Unknown"].index(data.get("had_will_str", "Unknown")),
        )
        data["had_will_str"] = data["had_will"]
        data["had_will"] = data["had_will"] == "Yes"

        data["estimated_estate_value"] = st.selectbox(
            "Estimated total estate value (approximate)",
            options=ESTATE_VALUES,
            index=ESTATE_VALUES.index(data.get("estimated_estate_value", "$100k–$500k")) if data.get("estimated_estate_value") in ESTATE_VALUES else 2,
        )
        data["has_real_property"] = st.checkbox("Did the deceased own real estate (home, land)?", value=data.get("has_real_property", False))
        data["has_minor_children"] = st.checkbox("Are there minor children (under 18)?", value=data.get("has_minor_children", False))
        data["has_business_interests"] = st.checkbox("Did the deceased own a business or business interests?", value=data.get("has_business_interests", False))
        data["has_trust"] = st.checkbox("Was there a revocable living trust?", value=data.get("has_trust", False))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.intake_step = 1
                st.rerun()
        with col2:
            if st.button("Next →", type="primary"):
                st.session_state.intake_step = 3
                st.rerun()

    # ── Step 3: Executor Info ──────────────────────────────────────────────
    elif step == 3:
        st.subheader("Executor / Personal Representative")
        st.caption("The executor is the person authorized to manage the estate.")

        data["executor_name"] = st.text_input("Your full name (executor)", value=data.get("executor_name", ""))
        data["executor_address"] = st.text_input("Mailing address (street)", value=data.get("executor_address", ""))
        data["executor_city_state_zip"] = st.text_input("City, State, ZIP", value=data.get("executor_city_state_zip", ""))
        col1, col2 = st.columns(2)
        with col1:
            data["executor_phone"] = st.text_input("Phone number", value=data.get("executor_phone", ""))
        with col2:
            data["executor_email"] = st.text_input("Email address", value=data.get("executor_email", ""))
        data["social_security_number_last4"] = st.text_input(
            "Last 4 digits of deceased's Social Security Number (for letters)",
            max_chars=4,
            type="password",
            value=data.get("social_security_number_last4", ""),
            help="Stored encrypted in your OS keychain-protected local storage. Never transmitted.",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.intake_step = 2
                st.rerun()
        with col2:
            if st.button("Next →", type="primary"):
                if not data.get("executor_name"):
                    st.error("Please enter the executor's name.")
                else:
                    st.session_state.intake_step = 4
                    st.rerun()

    # ── Step 4: Financial Accounts ─────────────────────────────────────────
    elif step == 4:
        st.subheader("Financial Accounts")
        st.caption("List the banks and financial institutions where the deceased held accounts. You can add more later.")

        existing = data.get("financial_accounts_text", "")
        accounts_text = st.text_area(
            "List each financial institution on a new line (e.g., Chase Bank, Fidelity, Vanguard)",
            value=existing, height=150,
            placeholder="Chase Bank\nFidelity\nVanguard\nChase Visa"
        )
        data["financial_accounts_text"] = accounts_text
        data["financial_accounts"] = [a.strip() for a in accounts_text.split("\n") if a.strip()]

        num_vehicles = st.number_input("Number of vehicles owned", min_value=0, max_value=20, value=len(data.get("vehicles", [])))
        vehicles = []
        for i in range(int(num_vehicles)):
            v = st.text_input(f"Vehicle {i+1} (Year Make Model)", value=data.get("vehicles", [None]*20)[i] if i < len(data.get("vehicles", [])) else "", key=f"vehicle_{i}")
            if v:
                vehicles.append(v)
        data["vehicles"] = vehicles

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.intake_step = 3
                st.rerun()
        with col2:
            if st.button("Next →", type="primary"):
                st.session_state.intake_step = 5
                st.rerun()

    # ── Step 5: Insurance ──────────────────────────────────────────────────
    elif step == 5:
        st.subheader("Insurance Policies")
        st.caption("List insurance companies where the deceased had policies.")

        existing = data.get("insurance_text", "")
        ins_text = st.text_area(
            "List each insurance company on a new line",
            value=existing, height=120,
            placeholder="MetLife (life insurance)\nBlue Cross (health)\nState Farm (auto & home)\nPrudential (annuity)"
        )
        data["insurance_text"] = ins_text
        data["insurance_policies"] = [a.strip() for a in ins_text.split("\n") if a.strip()]

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.intake_step = 4
                st.rerun()
        with col2:
            if st.button("Next →", type="primary"):
                st.session_state.intake_step = 6
                st.rerun()

    # ── Step 6: Digital Accounts ───────────────────────────────────────────
    elif step == 6:
        st.subheader("Digital Accounts")
        st.caption("Select all online accounts the deceased used. These each need to be closed or memorialized.")

        selected = st.multiselect(
            "Select all that apply",
            options=DIGITAL_PLATFORMS,
            default=data.get("digital_accounts", []),
        )
        data["digital_accounts"] = selected

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.intake_step = 5
                st.rerun()
        with col2:
            if st.button("Next →", type="primary"):
                st.session_state.intake_step = 7
                st.rerun()

    # ── Step 7: Review & Save ──────────────────────────────────────────────
    elif step == 7:
        st.subheader("Review & Save")
        st.caption("Review the information below, then save to generate your personalized estate checklist.")

        with st.expander("Deceased Information", expanded=True):
            st.write(f"**Name:** {data.get('full_name')}")
            st.write(f"**Date of birth:** {data.get('date_of_birth')}")
            st.write(f"**Date of death:** {data.get('date_of_death')}")
            st.write(f"**State:** {data.get('state_of_residence')} — {data.get('county', '')} County")
            st.write(f"**Veteran:** {'Yes' if data.get('is_veteran') else 'No'}")

        with st.expander("Estate Details"):
            st.write(f"**Had a will:** {'Yes' if data.get('had_will') else 'No'}")
            st.write(f"**Estimated value:** {data.get('estimated_estate_value')}")
            st.write(f"**Real property:** {'Yes' if data.get('has_real_property') else 'No'}")
            st.write(f"**Minor children:** {'Yes' if data.get('has_minor_children') else 'No'}")
            st.write(f"**Trust:** {'Yes' if data.get('has_trust') else 'No'}")

        with st.expander("Executor"):
            st.write(f"**Name:** {data.get('executor_name')}")
            st.write(f"**Address:** {data.get('executor_address')}, {data.get('executor_city_state_zip')}")
            st.write(f"**Phone:** {data.get('executor_phone')} | **Email:** {data.get('executor_email')}")

        with st.expander("Accounts & Assets"):
            st.write(f"**Financial accounts:** {', '.join(data.get('financial_accounts', [])) or 'None listed'}")
            st.write(f"**Insurance policies:** {', '.join(data.get('insurance_policies', [])) or 'None listed'}")
            st.write(f"**Vehicles:** {', '.join(data.get('vehicles', [])) or 'None listed'}")
            st.write(f"**Digital accounts:** {', '.join(data.get('digital_accounts', [])) or 'None listed'}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.intake_step = 6
                st.rerun()
        with col2:
            if st.button("Save & Generate Checklist", type="primary"):
                with st.spinner("Saving profile and generating your personalized checklist..."):
                    profile = DeceasedProfile(
                        full_name=data.get("full_name", ""),
                        date_of_birth=str(data.get("date_of_birth", "")),
                        date_of_death=str(data.get("date_of_death", "")),
                        state_of_residence=data.get("state_of_residence", ""),
                        county=data.get("county", ""),
                        had_will=data.get("had_will", False),
                        is_veteran=data.get("is_veteran", False),
                        executor_name=data.get("executor_name", ""),
                        executor_address=data.get("executor_address", ""),
                        executor_city_state_zip=data.get("executor_city_state_zip", ""),
                        executor_email=data.get("executor_email", ""),
                        executor_phone=data.get("executor_phone", ""),
                        social_security_number_last4=data.get("social_security_number_last4", ""),
                        estimated_estate_value=data.get("estimated_estate_value", ""),
                        has_real_property=data.get("has_real_property", False),
                        has_minor_children=data.get("has_minor_children", False),
                        has_business_interests=data.get("has_business_interests", False),
                        has_trust=data.get("has_trust", False),
                        financial_accounts=data.get("financial_accounts", []),
                        insurance_policies=data.get("insurance_policies", []),
                        vehicles=data.get("vehicles", []),
                        digital_accounts=data.get("digital_accounts", []),
                    )
                    save_profile(profile)
                    tasks = generate_task_list(profile)
                    calculate_deadlines(profile)
                    log_activity("intake_complete", f"Estate profile saved for {profile.full_name}. {len(tasks)} tasks generated.")
                    st.session_state.profile = profile
                    st.session_state.intake_complete = True

                st.success(f"Profile saved! Generated {len(tasks)} personalized tasks. Navigate to **Checklist** or **Home** to get started.")
                st.balloons()
