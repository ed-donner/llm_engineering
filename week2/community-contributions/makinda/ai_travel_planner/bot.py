"""Telegram bot: parse 'Destination, N days, Budget' and return itinerary."""
import os
import re
from dotenv import load_dotenv

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    raise SystemExit(
        "Missing 'telegram' package. Use the same Python that runs this script:\n"
        "  If using a venv: activate it first (e.g. source .venv/bin/activate), then:\n"
        "    pip install python-telegram-bot\n"
        "  Or with full path: /path/to/.venv/bin/python -m pip install python-telegram-bot\n"
        "Then run: python main.py --bot (with venv still active)"
    ) from None

from planner import generate_travel_plan

load_dotenv()


def parse_input(text: str) -> tuple[str | None, int | None, int | None]:
    """Parse 'Mombasa, 3 days, 1000' into (destination, days, budget)."""
    text = text.strip()
    # Match: "Place, N days, Budget" or "Place, N days, Budget currency"
    m = re.match(r"^(.+?),\s*(\d+)\s*days?\s*,\s*(\d+)\s*$", text, re.IGNORECASE)
    if m:
        dest, days, budget = m.group(1).strip(), int(m.group(2)), int(m.group(3))
        if 1 <= days <= 30 and budget > 0:
            return dest, days, budget
    # Relaxed: "Place, N, Budget"
    parts = [p.strip() for p in re.split(r",\s*", text, maxsplit=2)]
    if len(parts) == 3:
        try:
            d = parts[0]
            n = int(re.search(r"\d+", parts[1]).group()) if re.search(r"\d+", parts[1]) else 1
            b = int(re.search(r"\d+", parts[2]).group()) if re.search(r"\d+", parts[2]) else 0
            if d and 1 <= n <= 30 and b > 0:
                return d, n, b
        except (ValueError, AttributeError):
            pass
    return None, None, None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send: Destination, number of days, budget\nExample: Mombasa, 3 days, 1000"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dest, days, budget = parse_input(update.message.text or "")
    if dest is None:
        await update.message.reply_text("Use format: Destination, N days, Budget (e.g. Mombasa, 3 days, 1000)")
        return
    user_id = str(update.effective_user.id) if update.effective_user else "telegram"
    msg = await update.message.reply_text("Planning your trip…")
    response = generate_travel_plan(dest, days, budget, user_id)
    await msg.edit_text(response[:4000])


def run_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)
