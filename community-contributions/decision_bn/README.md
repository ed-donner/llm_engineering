# Decision Analysis Web App

A Streamlit application for Bayesian Network-based decision analysis.

## Developer

Created and maintained by **Sina Bahrami**.

## License

This project is distributed under the **Business Source License 1.1 (BSL 1.1)**.
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

## How to run the app
1. Create your .env file that includes your OpenAI and other LLM API keys (you can set a different API by modifying APP_CONFIG in config.py)
2. Create a virtual env by `python -m venv venv` and activate the venv
3. Install the dependencies by `pip install -r requirements.txt`
4. Simply run the streamlit app using `streamlit run app.py`
