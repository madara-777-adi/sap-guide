import re

from app.prompts import NOT_FOUND

SUPERVISOR_NOTE = "Check with your supervisor first."
RISKY = re.compile(r"\b(revers\w*|cancel\w*|delet\w*|undo)\b", re.IGNORECASE)


def add_safety_note(question: str, answer: str) -> str:
    """Append the supervisor warning for risky topics, whatever the model did."""
    if answer.strip() == NOT_FOUND:
        return answer
    if SUPERVISOR_NOTE.lower() in answer.lower():
        return answer
    if RISKY.search(question) or RISKY.search(answer):
        return f"{answer}\n\n{SUPERVISOR_NOTE}"
    return answer