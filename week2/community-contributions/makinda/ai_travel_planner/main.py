"""Start Telegram bot and/or Gradio. Usage: python main.py [--bot] [--gradio] (default: both)."""
import argparse
import threading


def main():
    p = argparse.ArgumentParser(description="AI Travel Planner")
    p.add_argument("--bot", action="store_true", help="Run Telegram bot only")
    p.add_argument("--gradio", action="store_true", help="Run Gradio UI only")
    args = p.parse_args()
    run_bot = args.bot or (not args.bot and not args.gradio)
    run_gradio = args.gradio or (not args.bot and not args.gradio)

    if run_bot and run_gradio:
        from bot import run_bot as start_bot
        t = threading.Thread(target=start_bot, daemon=True)
        t.start()
        from app import build_and_launch
        build_and_launch()
    elif run_bot:
        from bot import run_bot
        run_bot()
    else:
        from app import build_and_launch
        build_and_launch()


if __name__ == "__main__":
    main()
