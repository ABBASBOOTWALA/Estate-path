"""
Orchestrator Agent — routes user intent to specialist agents and manages the chat loop.
"""
from core.storage import load_profile, load_tasks
from core.claude_client import ask_claude_with_history
from agents.checklist_agent import get_progress_summary, get_next_recommended
from agents.deadline_agent import get_urgent_deadlines


def _build_system_prompt() -> str:
    profile = load_profile()
    if not profile:
        return (
            "You are EstatePath, a compassionate estate settlement assistant. "
            "The user has not yet completed the estate intake. "
            "Kindly ask them to complete the intake form first so you can provide personalized guidance. "
            "You can still answer general questions about the estate settlement process."
        )

    summary = get_progress_summary()
    urgent = get_urgent_deadlines(30)
    next_tasks = get_next_recommended(3)

    urgent_str = ", ".join(d.title for d in urgent[:3]) or "none"
    next_str = ", ".join(t.title for t in next_tasks) or "none"

    return f"""You are EstatePath, a compassionate and highly organized estate settlement assistant.
You are helping with the estate of {profile.full_name}, who passed away on {profile.date_of_death} in {profile.state_of_residence}.
The executor is {profile.executor_name}.

Current estate status:
- Total tasks: {summary['total']}
- Completed: {summary['completed']} ({summary['pct_complete']}%)
- Overdue: {summary['overdue']}
- Upcoming deadlines in 30 days: {summary['urgent_due_soon']}
- Blocked: {summary['blocked']}
- Urgent deadlines: {urgent_str}
- Recommended next steps: {next_str}

Guidelines:
- Always be warm, clear, and practical. The people using this tool are grieving.
- Avoid legal jargon. Explain what needs to happen and why.
- Break complex steps into simple, actionable items.
- Never provide legal advice — recommend consulting a probate attorney for legal questions.
- If asked about deadlines, refer to the specific state ({profile.state_of_residence}) rules.
- If asked what to do first, lead with urgent/high-priority tasks.
- Keep responses focused and under 300 words unless the user asks for detail.
- End each response with one specific, actionable next step."""


def chat(history: list) -> str:
    """
    Send a message to the orchestrator and get a response.
    history: list of {"role": "user"/"assistant", "content": str}
    """
    system = _build_system_prompt()
    return ask_claude_with_history(system, history)


def answer_question(question: str, history: list = None) -> str:
    """Single-question interface for quick answers."""
    if history is None:
        history = []
    history = history + [{"role": "user", "content": question}]
    return chat(history)
