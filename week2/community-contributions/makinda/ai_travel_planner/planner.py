"""AI travel plan generation; single entry point for Telegram and Gradio."""
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

from database import init_db, save_trip

load_dotenv()
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-4o-mini"


def _get_client():
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key, base_url=OPENROUTER_BASE)


def _mock_plan(destination: str, days: int, budget: int) -> str:
    """Deterministic mock when no API key."""
    per_day = budget // days if days else 0
    lines = [f"# {destination} – {days} day(s), budget ${budget}\n"]
    for d in range(1, days + 1):
        lines.append(f"\n## Day {d}\n- Morning: Explore {destination}\n- Afternoon: Local sights\n- Evening: Rest")
    lines.append("\n## Budget Breakdown\n")
    lines.append(f"- Accommodation: ${per_day * 40 // 100}\n- Food: ${per_day * 35 // 100}\n- Transport: ${per_day * 25 // 100}\n")
    lines.append("\n## Tips\n- Book in advance. Pack light. Check local weather.")
    return "\n".join(lines)


def generate_travel_plan(destination: str, days: int, budget: int, user_id: str = "gradio") -> str:
    """
    Generate itinerary, budget breakdown, and tips. Persist to sqlite3.
    Called by both Telegram bot and Gradio; no duplicated logic.
    """
    init_db()
    client = _get_client()
    prompt = (
        f"Create a travel plan for {destination}, {days} days, budget ${budget}. "
        "Reply with: Day 1 / Day 2 ... (2-3 activities per day), "
        "then 'Budget Breakdown:' (Accommodation, Food, Transport), then 'Tips:' (2-3 short tips). "
        "Use clear headings and bullet points. Be concise."
    )
    if client:
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
            )
            response = (r.choices[0].message.content or "").strip()
        except Exception:
            response = _mock_plan(destination, days, budget)
    else:
        response = _mock_plan(destination, days, budget)
    save_trip(user_id, destination, days, budget, response)
    return response
