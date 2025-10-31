#!/usr/bin/env python3
"""
Deal Intel launcher script
- ui: launch Gradio UI from price_is_right_final.App
- run: execute one planner cycle and print resulting opportunities
- keepwarm: ping Modal Pricer.wake_up to keep container warm
"""
import argparse
import sys
import time
from datetime import datetime
from logging_utils import init_logger
logger = init_logger("DealIntel.Launcher")

def launch_ui():
    from price_is_right_final import App
    logger.info("Launching UI")
    App().run()

def run_once():
    from deal_agent_framework import DealAgentFramework
    fw = DealAgentFramework()
    fw.init_agents_as_needed()
    logger.info("Running planner once")
    opportunities = fw.run()
    logger.info(f"Opportunities in memory: {len(opportunities)}")
    if opportunities:
        last = opportunities[-1]
        logger.info(f"Last opportunity: price=${last.deal.price:.2f}, estimate=${last.estimate:.2f}, discount=${last.discount:.2f}")
        logger.info(f"URL: {last.deal.url}")
        logger.info(f"Description: {last.deal.product_description[:120]}...")

def keep_warm(interval_sec: int = 30):
    import modal
    logger.info("Starting keep-warm loop for Modal Pricer")
    try:
        Pricer = modal.Cls.from_name("pricer-service", "Pricer")
    except Exception:
        Pricer = modal.Cls.lookup("pricer-service", "Pricer")
    pricer = Pricer()
    try:
        while True:
            reply = pricer.wake_up.remote()
            logger.info(f"Wake-up reply: {reply}")
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        logger.info("Keep-warm loop stopped")

def health():
    logger.info("Running health checks")
    from health_check import run_all
    ok = run_all()
    if not ok:
        logger.warning("Health checks failed")
        raise SystemExit(1)
    logger.info("Health checks passed")

def main(argv=None):
    parser = argparse.ArgumentParser(description="Deal Intel Launcher")
    parser.add_argument("command", choices=["ui", "run", "keepwarm", "health"], help="Command to execute")
    parser.add_argument("--interval", type=int, default=30, help="Keep-warm ping interval (seconds)")
    args = parser.parse_args(argv)

    if args.command == "ui":
        launch_ui()
    elif args.command == "run":
        run_once()
    elif args.command == "keepwarm":
        keep_warm(args.interval)
    elif args.command == "health":
        health()

if __name__ == "__main__":
    main()