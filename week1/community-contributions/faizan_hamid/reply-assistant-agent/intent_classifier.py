def detect_intent(message: str) -> str:
    """
    Detect the likely intent/category of the incoming message
    using simple keyword-based rules.
    """
    if not message:
        return "unknown"

    text = message.lower()

    if any(keyword in text for keyword in ["interview", "availability", "schedule an interview", "interview discussion"]):
        return "interview_invitation"

    if any(keyword in text for keyword in ["opportunity", "role", "position", "resume", "profile", "opening"]):
        return "recruiter_outreach"

    if any(keyword in text for keyword in ["follow up", "following up", "just checking", "checking in"]):
        return "follow_up"

    if any(keyword in text for keyword in ["leave", "pto", "day off", "sick leave", "medical leave"]):
        return "leave_related"

    if any(keyword in text for keyword in ["meeting", "call", "connect", "discussion", "zoom", "google meet"]):
        return "meeting_request"

    return "general_professional_message"


def suggest_reply_goal(intent: str) -> str:
    """
    Suggest a reply goal based on the detected intent.
    """
    reply_goals = {
        "interview_invitation": "accept_and_share_availability",
        "recruiter_outreach": "show_interest_and_request_more_details",
        "follow_up": "respond_politely_with_status_or_next_step",
        "leave_related": "reply_professionally_and_acknowledge",
        "meeting_request": "accept_or_propose_availability",
        "general_professional_message": "reply_clearly_and_professionally",
        "unknown": "reply_clearly_and_professionally"
    }

    return reply_goals.get(intent, "reply_clearly_and_professionally")