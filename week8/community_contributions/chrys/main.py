"""ARIA CLI: run-once, schedule, or trigger."""
import sys
import os

# Ensure chrys directory is on path when run from repo root or week8
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

import argparse
import logging
from dotenv import load_dotenv

load_dotenv()

from orchestrator import run_pipeline
from scheduler import start_scheduler


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    parser = argparse.ArgumentParser(description="ARIA Market Intelligence & Alert")
    parser.add_argument("command", choices=["run-once", "schedule", "trigger"], nargs="?", default="run-once")
    args = parser.parse_args()
    if args.command in ("run-once", "trigger"):
        run_pipeline()
    else:
        start_scheduler()
        try:
            import time
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
