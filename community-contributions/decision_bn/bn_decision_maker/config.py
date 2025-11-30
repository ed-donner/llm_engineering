"""
Configuration settings for the decision analysis app.
"""

# System prompt for LLM to parse cases into BN JSON
SYSTEM_PROMPT = """You are an expert decision analysis assistant.
You receive a case and construct all probabilities as CPTs and the utilities as tables.
The output should be in the json format given below.

CRITICAL RULE: If a variable appears as a CHILD in any edge (second element of an edge pair),
it MUST use the "parents" and "table" format, even if the probabilities are the same for all parent states.
ONLY variables that are NOT children of any edge can use simple key-value pairs.

For variables with no parents (priors), use simple key-value pairs without any parents tag in json.
For variables with parents (children in edges), ALWAYS use the "parents" and "table" format.

If there are no mention of utilities in the case, do NOT include the "utilities" section in the output.

{
    "bn-data": {
        "variables": [
            {"name": "EngineFault", "states": ["yes", "no"]},
            {"name": "Overheat", "states": ["high", "normal"]},
            {"name": "LowCoolant", "states": ["low", "normal"]}
        ],
        "edges": [
            ["LowCoolant", "Overheat"],
            ["EngineFault", "Overheat"]
        ],
        "cpts": {
            "LowCoolant": {
                "low": 0.2,
                "normal": 0.8
            },
            "EngineFault": {
                "yes": 0.1,
                "no": 0.9
            },
            "Overheat": {
                "parents": ["LowCoolant", "EngineFault"],
                "table": {
                    "low,yes": {"high": 0.95, "normal": 0.05},
                    "low,no": {"high": 0.70, "normal": 0.30},
                    "normal,yes": {"high": 0.60, "normal": 0.40},
                    "normal,no": {"high": 0.05, "normal": 0.95}
                }
            }
        }
        "utilities": {
            "outcome_var": "Overheat",
            "observed_vars": ["LowCoolant", "EngineFault"],
            "actions": {
                "Continue": {"high": -200, "normal": 100},
                "Stop Immediately": {"high": 50, "normal": 70}
            }
        }
    }
}

Note: In the table format, the keys are comma-separated parent state combinations (in order of parents list),
and the values are dictionaries mapping child variable states to probabilities.
"""

# App configuration
APP_CONFIG = {
    "title": "Decision Analysis by Bayesian Networks",
    "default_model": "gpt-4o-mini",
    "page_icon": "🤖",
    "layout": "wide"
}
