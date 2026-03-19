# Agentic Code Review Assistant

A multi-agent system for intelligent, automated code review using Python static analysis and optional LLM integration.

## Overview

This exercise demonstrates an autonomous agentic architecture where specialized agents collaborate to perform comprehensive code reviews. Each agent focuses on a specific aspect of code quality, and an orchestrator coordinates their work to produce a unified review report.

## Architecture

```
                    ┌─────────────────────────┐
                    │   CodeReviewOrchestrator│
                    └───────────┬─────────────┘
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│  Syntax   │ │ Security  │ │   Style   │ │   Docs    │ │    LLM    │
│  Agent    │ │   Agent   │ │   Agent   │ │   Agent   │ │   Agent   │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
```

## Agents

### 1. SyntaxAnalyzerAgent
- Parses Python AST for structural analysis
- Counts functions, classes, imports
- Detects syntax errors
- Checks line length and whitespace issues

### 2. SecurityAnalyzerAgent
- Scans for dangerous patterns (eval, exec, os.system)
- Detects hardcoded credentials
- Identifies injection vulnerabilities
- Flags unsafe deserialization

### 3. StyleAnalyzerAgent
- Checks PEP8 compliance
- Validates naming conventions
- Verifies proper indentation
- Detects style inconsistencies

### 4. DocumentationAnalyzerAgent
- Checks for module docstrings
- Validates function/class documentation
- Calculates documentation coverage
- Identifies undocumented code

### 5. LLMReviewAgent (Optional)
- Uses Claude or GPT for intelligent analysis
- Provides contextual suggestions
- Identifies potential bugs
- Generates human-readable summaries

## Installation

```bash
pip install anthropic openai  # For LLM features (optional)
```

## Usage

### Basic Usage (Without LLM)

```python
from agentic_code_review_assistant import CodeReviewOrchestrator, format_review_report

code = '''
def my_function(x, y):
    return x + y
'''

orchestrator = CodeReviewOrchestrator(enable_llm=False)
result = orchestrator.review(code, "my_code.py")
print(format_review_report(result))
```

### With LLM Integration

```python
import os
os.environ["ANTHROPIC_API_KEY"] = "your-api-key"

orchestrator = CodeReviewOrchestrator(enable_llm=True)
result = orchestrator.review(code, "my_code.py")
```

## Output Example

```
============================================================
CODE REVIEW REPORT: sample_code.py
============================================================

Overall Score: 75/100
Summary: Review Score: 75/100 | warning: 3 | error: 2 | info: 2

----------------------------------------
METRICS
----------------------------------------
  total_lines: 25
  functions: 3
  classes: 1
  documentation_coverage: 33.3%

----------------------------------------
ISSUES FOUND (7)
----------------------------------------

  [ERROR]
    Line 15: Use of eval() is dangerous - can execute arbitrary code
      -> Review and remediate this security concern

  [WARNING]
    Line 8: Function 'AddItem' should use snake_case
      -> Rename to use lowercase with underscores
```

## Key Concepts Demonstrated

1. **Multi-Agent Architecture**: Specialized agents with single responsibilities
2. **Agent Orchestration**: Central coordinator managing agent execution
3. **Issue Aggregation**: Combining findings from multiple sources
4. **Severity Classification**: Prioritizing issues by impact
5. **LLM Integration**: Optional AI-powered intelligent analysis
6. **Extensibility**: Easy to add new agents or modify existing ones

## Extending the System

To add a new agent:

```python
class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyCustomAgent")
    
    def analyze(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log("Running custom analysis...")
        issues = []
        # Your analysis logic here
        return {"issues": issues, "metrics": {...}}

# Add to orchestrator
orchestrator.agents.append(MyCustomAgent())
```

## Future Enhancements

- [ ] Git integration for reviewing diffs
- [ ] Support for multiple programming languages
- [ ] Custom rule configuration
- [ ] CI/CD pipeline integration
- [ ] Historical trend analysis

## Author

Emmanuel Ochade - Week 8 Community Contribution
