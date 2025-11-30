# Architecture Overview

## Production Web App Structure

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│                     (Streamlit UI)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                      app.py                                  │
│  • UI State Management (session_state)                      │
│  • User Input Collection                                    │
│  • Results Display & Visualization                          │
└───────┬─────────────────────────┬────────────────────┬───────┘
        │                         │                    │
        ▼                         ▼                    ▼
┌──────────────┐         ┌──────────────┐    ┌────────────────┐
│llm_parser.py │         │decision_     │    │config.py       │
│              │         │maker.py      │    │                │
│CaseParser    │         │              │    │• Prompts       │
│class:        │         │DecisionBN    │    │• Settings      │
│• parse_case()│         │class:        │    │• Constants     │
│• validate()  │         │• build BN    │    └────────────────┘
│              │         │• inference   │
│              │         │• utilities   │
└──────┬───────┘         └──────┬───────┘
       │                        │
       ▼                        ▼
┌──────────────┐         ┌──────────────┐    ┌────────────────┐
│litellm       │         │pyagrum       │    │examples/       │
│(LLM API)     │         │(BN Engine)   │    │                │
│              │         │              │    │predefined_     │
│OpenAI        │         │LazyProp      │    │cases.py        │
│Claude etc.   │         │Inference     │    │                │
└──────────────┘         └──────────────┘    └────────────────┘
```

## Data Flow

### 1. Case Analysis Flow
```
User Input (text)
    ↓
CaseParser.parse_case()
    ↓
LLM API Call (OpenAI/Claude)
    ↓
JSON Structure Validation
    ↓
DecisionBN.__init__()
    ↓
pyAgrum BN Construction
    ↓
Store in session_state
```

### 2. Query Flow
```
User selects variable + evidence
    ↓
DecisionBN.get_posterior()
    ↓
pyAgrum LazyPropagation inference
    ↓
Display results + charts
```

### 3. Decision Analysis Flow
```
Predefined utilities loaded
    ↓
DecisionBN.compute_expected_utilities()
    ↓
For each action:
    EU = Σ P(outcome|evidence) × U(action, outcome)
    ↓
DecisionBN.get_optimal_action()
    ↓
Display recommendation
```

## Module Responsibilities

### app.py (Presentation Layer)
- ✓ UI layout and widgets
- ✓ Session state management
- ✓ User input validation
- ✓ Results visualization
- ✗ NO business logic
- ✗ NO direct LLM calls
- ✗ NO BN construction

### bn_decision_maker.py (Core Logic)
- ✓ BN data structure → pyAgrum conversion
- ✓ Inference queries (marginals, posteriors)
- ✓ Expected utility calculations
- ✓ Optimal action selection
- ✗ NO UI code
- ✗ NO LLM interaction

### llm_parser.py (External Service)
- ✓ LLM API interaction
- ✓ JSON parsing & validation
- ✓ Error handling for API calls
- ✗ NO UI code
- ✗ NO BN operations

### config.py (Configuration)
- ✓ System prompts
- ✓ App settings
- ✓ Constants
- ✗ NO logic

### examples/ (Data)
- ✓ Predefined case descriptions
- ✓ Utility mappings
- ✗ NO logic

## Benefits of This Architecture

### 1. **Testability**
- Each module can be tested independently
- No need for Streamlit to test core logic
- Mock LLM responses easily

### 2. **Maintainability**
- Clear separation of concerns
- Easy to locate and fix bugs
- Changes in one layer don't affect others

### 3. **Reusability**
- `DecisionBN` works in notebooks, CLI, APIs
- `CaseParser` can be used in batch processing
- Core logic independent of UI framework

### 4. **Scalability**
- Easy to add new case types
- Simple to swap LLM providers
- Can replace Streamlit with FastAPI/Flask

### 5. **Debugging**
- Each layer has clear inputs/outputs
- Can test components in isolation
- Error messages point to specific modules

## Usage Patterns

### Pattern 1: Web App (Current)
```python
# In app.py
from bn_decision_maker import CaseParser, DecisionBN, SYSTEM_PROMPT
parser = CaseParser()
data = parser.parse_case(text, SYSTEM_PROMPT)
bn = DecisionBN(data['bn-data'])
result = bn.get_optimal_action(...)
```

### Pattern 2: Notebook Exploration
```python
# In Jupyter
from bn_decision_maker import DecisionBN
bn = DecisionBN(my_bn_data)
bn.get_marginal("Variable")
```

### Pattern 3: CLI Tool
```python
# In cli.py
import sys
from bn_decision_maker import CaseParser, DecisionBN, SYSTEM_PROMPT

text = sys.stdin.read()
parser = CaseParser()
data = parser.parse_case(text, PROMPT)
bn = DecisionBN(data['bn-data'])
print(bn.get_optimal_action(...))
```

### Pattern 4: REST API
```python
# In api.py (FastAPI)
from bn_decision_maker import CaseParser, DecisionBN, SYSTEM_PROMPT

@app.post("/analyze")
def analyze(case: str):
    parser = CaseParser()
    data = parser.parse_case(case, PROMPT)
    bn = DecisionBN(data['bn-data'])
    return bn.compute_expected_utilities(...)
```

## Testing Strategy

### Unit Tests
- `test_decision_maker.py`: Test DecisionBN class
- `test_llm_parser.py`: Test parsing & validation
- `test_utilities.py`: Test EU calculations

### Integration Tests
- End-to-end case analysis
- LLM → BN → Decision pipeline

### Manual Tests
- Run `test_decision_maker.py`
- Use Streamlit app with predefined cases
- Try custom cases

## Future Enhancements

1. **Caching**: Add `@lru_cache` to expensive operations
2. **Async**: Use async LLM calls for faster responses
3. **Visualization**: Add network graph visualization
4. **Export**: Save BN models to files
5. **Batch**: Process multiple cases
6. **API**: REST API wrapper
7. **Docker**: Containerize the app
