---
title: Decision BN Analyzer
emoji: 🎯
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 8501
pinned: false
---

# Decision Analysis Web App

A production-ready Streamlit application for Bayesian Network-based decision analysis.

## Developer

Created and maintained by **Sina Bahrami**.

## License

This project is distributed under the **Business Source License 1.1 (BSL 1.1)**.

Key points:
- Free for non-production, personal, research, academic, or internal evaluation use.
- Any production or commercial use (hosting, resale, paid integration, revenue-generating workflows) requires a separate commercial agreement with the Licensor before the Change Date.
- **Change Date:** 2027-12-31 — on this date the license automatically converts to the MIT License.
- **Future License (Change License):** MIT.

See the full terms in [`LICENSE`](./LICENSE). For commercial inquiries, contact the developer.

## Architecture

```
week1/
├── app.py                              # Streamlit UI (thin presentation layer)
├── bn_decision_maker/                  # Core package
│   ├── __init__.py                    # Package exports
│   ├── bn_decision_maker.py           # Core BN logic (DecisionBN class)
│   ├── llm_parser.py                  # LLM interaction (CaseParser class)
│   ├── config.py                      # Configuration & prompts
│   └── examples/
│       ├── __init__.py
│       └── predefined_cases.py        # Sample cases & utilities
├── test_decision_maker.py             # Unit tests
└── README.md                          # This file
```

## Design Principles

### 1. **Separation of Concerns**
- **UI Layer** (`app.py`): Streamlit interface only
- **Business Logic** (`decision_maker.py`): BN construction, inference, utilities
- **External Services** (`llm_parser.py`): LLM API calls
- **Configuration** (`config.py`): Prompts, settings

### 2. **Testability**
- Core logic (`DecisionBN`) works without Streamlit
- Can be imported and used in notebooks, CLI, or other apps
- Easy to unit test each module independently

### 3. **Reusability**
- `DecisionBN` class can be used in any Python application
- LLM parsing separated from BN logic
- Predefined cases in separate module

## Usage

### Running the App

```bash
streamlit run app.py
```

### Using DecisionBN Programmatically

```python
from bn_decision_maker import DecisionBN

# From parsed JSON
bn_data = {...}  # Your BN structure
bn = DecisionBN(bn_data)

# Query marginals
marginal = bn.get_marginal("Overheat")

# Query with evidence
posterior = bn.get_posterior(["Overheat"], {"Coolant": "low"})

# Compute expected utilities
utilities = {
    "Continue": {"high": -200, "normal": 100},
    "Stop": {"high": 50, "normal": 70}
}
eus = bn.compute_expected_utilities("Overheat", utilities)
best_action, best_eu = bn.get_optimal_action("Overheat", utilities)
```

### Parsing Cases with LLM

```python
from bn_decision_maker import CaseParser, SYSTEM_PROMPT

parser = CaseParser()
parsed = parser.parse_case(case_text, SYSTEM_PROMPT)
bn_data = parsed['bn-data']
```

## Key Features

1. **Interactive UI**: Select predefined cases or enter custom ones
2. **LLM-Powered Parsing**: Automatically extracts BN structure from text
3. **Marginal & Posterior Queries**: Explore probability distributions
4. **Evidence Support**: Set evidence and see updated posteriors
5. **Decision Analysis**: Automatic expected utility calculation
6. **Visualization**: Charts for probabilities and utilities

## Extending the App

### Adding New Cases

Edit `bn_decision_maker/examples/predefined_cases.py`:

```python
CASE_MY_NEW_CASE = """..."""

PREDEFINED_CASES["My New Case"] = CASE_MY_NEW_CASE

CASE_UTILITIES["My New Case"] = {
    "outcome_var": "OutcomeVariable",
    "actions": {
        "Action1": {"state1": util1, "state2": util2},
        "Action2": {"state1": util3, "state2": util4}
    }
}
```

### Custom Validation

Add validation methods to `CaseParser._validate_bn_data()` in `bn_decision_maker/llm_parser.py`.

### Alternative LLM Models

Change the model in `config.py`:

```python
APP_CONFIG = {
    ...
    "default_model": "gpt-4o",  # or "claude-3-opus-20240229"
}
```

## Dependencies

- `streamlit`: Web UI
- `pyagrum`: Bayesian Network engine
- `litellm`: LLM API wrapper
- `pandas`: Data handling
- `python-dotenv`: Environment variables

## Environment Setup

Create `.env` file in project root:

```
OPENAI_API_KEY=sk-proj-...
```

## Notes

- The notebook (`decision_maker.ipynb`) is for prototyping only
- Production app uses only the Python modules
- BN structure validated on parse
- Session state maintains BN between Streamlit reruns
