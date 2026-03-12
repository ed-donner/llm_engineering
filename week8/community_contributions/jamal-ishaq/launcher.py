#!/usr/bin/env python3
import argparse

from resource_agent_framework import ResourceScoutFramework


def run_once(topic: str):
    framework = ResourceScoutFramework()
    latest_results = framework.run(topic=topic)
    print(f"Autonomous run complete. Top candidates this run: {len(latest_results)}")


def launch_ui():
    from ui import App

    App().run()


def main():
    parser = argparse.ArgumentParser(
        description="Study Resource Scout launcher (autonomous top-5 mode)"
    )
    parser.add_argument("command", choices=["run", "autorun", "ui"])
    parser.add_argument("--topic", default="llm agents")
    args = parser.parse_args()

    if args.command == "run":
        run_once(args.topic)
    else:
        launch_ui()


if __name__ == "__main__":
    main()
