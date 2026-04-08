"""
Chat page — conversational AI estate assistant.
"""
import streamlit as st
from core.storage import load_profile
from agents.orchestrator import chat as orchestrator_chat


SUGGESTED_QUESTIONS = [
    "What should I do first?",
    "How do I file for probate?",
    "What documents do I need for the life insurance claim?",
    "What is a letter testamentary?",
    "How long does estate settlement usually take?",
    "What debts is the estate responsible for?",
    "How do I transfer real estate to an heir?",
    "What are the tax obligations of the estate?",
]


def show():
    profile = load_profile()

    st.header("Ask EstatePath")
    st.caption("Your AI estate settlement guide. Ask anything about the process.")

    st.info(
        "💡 **EstatePath provides guidance and general information only — not legal advice.** "
        "For legal questions, please consult a licensed probate attorney in your state.",
        icon="⚖️"
    )

    # ── Initialize chat history ────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ── Suggested questions ────────────────────────────────────────────────
    if not st.session_state.chat_history:
        st.subheader("Suggested Questions")
        cols = st.columns(2)
        for idx, q in enumerate(SUGGESTED_QUESTIONS):
            with cols[idx % 2]:
                if st.button(q, key=f"suggest_{idx}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    with st.spinner("Thinking..."):
                        response = orchestrator_chat(st.session_state.chat_history)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
        st.divider()

    # ── Chat history ───────────────────────────────────────────────────────
    for message in st.session_state.chat_history:
        role = message["role"]
        with st.chat_message(role, avatar="🌿" if role == "assistant" else "👤"):
            st.markdown(message["content"])

    # ── Input ──────────────────────────────────────────────────────────────
    user_input = st.chat_input("Ask a question about the estate process...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner("Thinking..."):
                response = orchestrator_chat(st.session_state.chat_history)
            st.markdown(response)

        st.session_state.chat_history.append({"role": "assistant", "content": response})

    # ── Controls ───────────────────────────────────────────────────────────
    if st.session_state.chat_history:
        if st.button("Clear conversation", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()
