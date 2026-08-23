"""
Simple multi-agent pipeline for tope-ai-labs (based on week8 exercises).

Run from week8:
  python community_contributions/tope-ai-labs/week8/simple_multi_agent.py

Local LLM: set USE_LLM=true and OPENAI_API_KEY.
Modal: set USE_MODAL=true and run after: modal deploy community_contributions/tope-ai-labs/week8/modal_multi_agent.py
"""
import os
import sys

# Allow running as script: add this package dir so "from coordinator" works
_here = os.path.abspath(os.path.dirname(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from dotenv import load_dotenv
load_dotenv(override=True)

USE_LLM = os.getenv("USE_LLM", "false").lower() in ("1", "true", "yes")
USE_MODAL = os.getenv("USE_MODAL", "false").lower() in ("1", "true", "yes")

# Modal app/class names (must match modal_multi_agent.py)
MODAL_APP = "tope-ai-labs-multi-agent"
MODAL_CLASS = "MultiAgentPipeline"


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "multi-agent AI systems"

    if USE_MODAL:
        import modal
        Pipeline = modal.Cls.lookup(MODAL_APP, MODAL_CLASS)
        report = Pipeline().run.remote(topic)
        print(report)
        return

    from coordinator import CoordinatorAgent
    coordinator = CoordinatorAgent(use_llm=USE_LLM)
    report = coordinator.run(topic=topic)
    print(report)


if __name__ == "__main__":
    main()
