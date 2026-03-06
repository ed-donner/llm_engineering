import os
import json
import asyncio
import logging
from typing import Optional, List
from dotenv import load_dotenv
from openai import OpenAI

from schemas import PrescriptionInput, AgentReport, Finding, FinalVerdict
from tools.pharmacy_tools import (
    INTERACTION_TOOLS,
    DOSAGE_TOOLS,
    ALLERGY_TOOLS,
    CONTRAINDICATION_TOOLS,
    ALL_TOOLS,
    handle_tool_calls,
)

load_dotenv(override=True)


# ============================================================================
# BASE AGENT — logging helper (mirrors week8/agents/agent.py)
# ============================================================================

class Agent:
    """Lightweight base with coloured logging."""

    # Terminal colours
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    RED = '\033[31m'
    BG_BLACK = '\033[40m'
    RESET = '\033[0m'

    name: str = ""
    color: str = '\033[37m'

    def log(self, message: str):
        color_code = self.BG_BLACK + self.color
        logging.info(f"{color_code}[{self.name}] {message}{self.RESET}")


# ============================================================================
# TOOL-CALLING AGENT MIXIN
# ============================================================================

class ToolAgent(Agent):
    """
    Agent that follows the autonomous_planning_agent pattern:
    while finish_reason == "tool_calls" → dispatch → loop.
    Final response is parsed into a Pydantic model.
    """

    MODEL: str = "gpt-4o-mini"
    SYSTEM_PROMPT: str = ""
    tools: list = []          # JSON tool defs
    output_type = None        # Pydantic model for structured output
    max_turns: int = 10       # safety cap

    def __init__(self):
        self.openai = OpenAI()

    def run(self, user_input: str):
        """
        Execute the tool-calling loop and return a parsed Pydantic object.
        Mirrors autonomous_planning_agent.plan().
        """
        self.log(f"Starting run")
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        turns = 0
        done = False
        while not done and turns < self.max_turns:
            turns += 1

            # If we have tools, allow the model to call them; otherwise just parse
            if self.tools:
                response = self.openai.chat.completions.create(
                    model=self.MODEL,
                    messages=messages,
                    tools=self.tools,
                    temperature=0.5,
                )
            else:
                # No tools — single-shot structured output
                response = self.openai.chat.completions.parse(
                    model=self.MODEL,
                    messages=messages,
                    response_format=self.output_type,
                    temperature=0.5,
                )
                parsed = response.choices[0].message.parsed
                self.log(f"Completed (structured output, 1 turn)")
                return parsed

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                # Dispatch tool calls and feed results back
                tool_results = handle_tool_calls(choice.message)
                messages.append(choice.message)
                messages.extend(tool_results)
                self.log(f"Turn {turns}: called {len(choice.message.tool_calls)} tool(s)")
            else:
                # Model is done calling tools — now get structured output
                done = True

        # Final structured parse with accumulated context
        self.log(f"Generating final report after {turns} turn(s)")

        # Append the last assistant message if it had content
        if not done:
            self.log("Hit max turns — forcing final output")
        
        # Add the assistant's last text reply to context, then do a structured parse
        last_content = response.choices[0].message.content
        if last_content:
            messages.append({"role": "assistant", "content": last_content})

        messages.append({
            "role": "user",
            "content": "Based on all the tool results above, provide your final structured report now."
        })

        final_response = self.openai.chat.completions.parse(
            model=self.MODEL,
            messages=messages,
            response_format=self.output_type,
            temperature=0.3,
        )
        result = final_response.choices[0].message.parsed
        self.log(f"Completed with status: {getattr(result, 'status', 'N/A')}")
        return result


# ============================================================================
# SPECIALIST AGENTS
# ============================================================================

class InteractionAgent(ToolAgent):
    name = "InteractionChecker"
    color = Agent.CYAN
    MODEL = "gpt-4o"
    tools = INTERACTION_TOOLS
    output_type = AgentReport

    SYSTEM_PROMPT = """You are a specialist in detecting possible drug-drug interactions.
You will be given patient and prescription data. Use your tools to check for interactions.

Available tools:
- check_drug_interaction: Check pairwise interaction between two drugs
- check_multi_drug_interactions: Scan all drug pairs at once (pass JSON array of drug names)
- check_duplicate_therapy: Detect duplicate medications
- check_therapeutic_duplication: Detect class-level duplication via ATC codes
- normalize_drug_name: Resolve brand/generic names via RxNorm

Call the tools you need, then provide your final AgentReport."""


class DosageAgent(ToolAgent):
    name = "DosageChecker"
    color = Agent.YELLOW
    MODEL = "gpt-4o-mini"
    tools = DOSAGE_TOOLS
    output_type = AgentReport

    SYSTEM_PROMPT = """You are a specialist in validating drug dosages.
1. Calculate daily dose with calculate_daily_dose.
2. If patient is a child (<18), use check_pediatric_dosing.
3. If patient is elderly (65+), use check_geriatric_considerations.
4. If renal impairment, use check_renal_dosing.
5. If pregnant, use check_pregnancy_safety.

Call the relevant tools, then provide your final AgentReport."""


class AllergyAgent(ToolAgent):
    name = "AllergyChecker"
    color = Agent.RED
    MODEL = "gpt-4o"
    tools = ALLERGY_TOOLS
    output_type = AgentReport

    SYSTEM_PROMPT = """You are a specialist in detecting drug allergies and cross-sensitivity.
1. Use check_drug_allergy to compare each drug against patient allergies (comma-separated).
2. Use normalize_drug_name to resolve brand names to generic/ingredient level.
3. Use get_drug_label_info for additional ingredient details if needed.

Call the relevant tools, then provide your final AgentReport."""


class ContraindicationAgent(ToolAgent):
    name = "ContraindicationChecker"
    color = Agent.MAGENTA
    MODEL = "gpt-4o-mini"
    tools = CONTRAINDICATION_TOOLS
    output_type = AgentReport

    SYSTEM_PROMPT = """You are a specialist in detecting drug contraindications.
You will be given drugs and patient conditions.

Available tools:
- check_contraindication: Check if a drug is contraindicated for a condition
- check_drug_recall: Check FDA enforcement database for active recalls
- get_controlled_substance_info: Check DEA schedule
- normalize_drug_name: Resolve brand/generic names
- get_drug_label_info: Get full FDA label

Call the relevant tools, then provide your final AgentReport."""


class TriageAgent(ToolAgent):
    name = "TriageAgent"
    color = Agent.GREEN
    MODEL = "gpt-4o"
    tools = []  # No tools — pure extraction
    output_type = PrescriptionInput

    SYSTEM_PROMPT = """You are a medical triage expert.
Convert the natural language prescription data into a structured object.
Ensure you extract:
- Patient Age and Weight (essential for dosage)
- Patient Allergies and Conditions
- List of Drugs with Dosage and Frequency
If any information is missing or ambiguous, infer from context or leave minimal defaults."""


class VerdictAgent(ToolAgent):
    name = "FinalVerdictAgent"
    color = Agent.BLUE
    MODEL = "gpt-4o"
    tools = []  # No tools — synthesises reports
    output_type = FinalVerdict

    SYSTEM_PROMPT = """You are the Chief Pharmacist.
You will receive reports from the Interaction, Allergy, Dosage and Contraindication agents.
Synthesize them into a single final decision.

RULES:
1. If ANY agent flagged RED or CRITICAL → status MUST be RED (Do Not Dispense).
2. If YELLOW/WARNING issues → status YELLOW (Dispense with Counseling).
3. If all GREEN → status GREEN (Dispense).
4. Provide a clear, concise summary and specific actions."""


# ============================================================================
# CONVENIENCE INSTANCES — so app.py can import directly
# ============================================================================

triage_agent = TriageAgent()
interaction_agent = InteractionAgent()
allergy_agent = AllergyAgent()
dosage_agent = DosageAgent()
contraindication_agent = ContraindicationAgent()
verdict_agent = VerdictAgent()

