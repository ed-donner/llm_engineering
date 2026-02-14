# Step 4: Generation Service Implementation

## Overview

In this step, we implemented the **GeneratorService** - the orchestration layer that coordinates the entire synthetic data generation workflow. This is the "brain" that connects our backend (HuggingFace API), database (SQLAlchemy), and validation layers.

## What We Built

### 1. GeneratorService (`synth_data/services/generator.py`)

A comprehensive service that handles:
- Schema validation before generation
- Backend coordination (calling LLM APIs)
- Progress tracking with callbacks
- Database persistence (optional)
- Error handling and recovery
- Generation history management

### 2. Comprehensive Test Suite (`tests/test_generator.py`)

16 tests covering:
- Schema validation (6 tests)
- Generation workflow (6 tests)
- History retrieval (3 tests)
- Context manager functionality (1 test)

### 3. Demo Script (`demo_generator.py`)

Interactive demonstrations showing:
- Basic data generation
- History retrieval
- Custom parameters
- Error handling

## Key Concepts Explained

### Separation of Concerns

The architecture follows a clean separation:

```
┌─────────────────────────────────────────────┐
│           User / UI Layer                   │
│         (Streamlit - next step)             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│        GeneratorService (Step 4)            │
│     - Orchestrates the workflow             │
│     - Validates schemas                     │
│     - Handles errors                        │
│     - Manages progress                      │
└──────┬────────────────────────┬─────────────┘
       │                        │
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│   Backend    │         │   Database   │
│  (Step 2-3)  │         │   (Step 3)   │
│ - API calls  │         │ - Storage    │
│ - Parsing    │         │ - History    │
└──────────────┘         └──────────────┘
```

### Why This Design?

**1. Testability**
- Each component can be tested in isolation
- Mock backends for testing without API calls
- In-memory database for fast tests

**2. Maintainability**
- Changes to backend don't affect service layer
- Changes to database don't affect generation logic
- Easy to add new backends or storage options

**3. Extensibility**
- Add new backends by implementing ModelBackend interface
- Add validation rules without touching backends
- Add quality checks without modifying generation

## Code Walkthrough

### The Main `generate()` Method

```python
def generate(
    self,
    schema: Dict[str, Any],
    num_records: int,
    params: Optional[GenerationParams] = None,
    on_progress: Optional[Callable[[int, int], None]] = None
) -> Dict[str, Any]:
```

**Flow:**

1. **Validate Schema** (Fail Fast)
   ```python
   self._validate_schema(schema)  # Catch errors before API calls
   ```

2. **Progress: 0%**
   ```python
   if on_progress:
       on_progress(0, num_records)
   ```

3. **Call Backend** (The expensive operation)
   ```python
   result = self.backend.generate(schema, num_records, params)
   ```

4. **Progress: 100%**
   ```python
   if on_progress:
       on_progress(result.num_records, num_records)
   ```

5. **Save to Database** (Optional)
   ```python
   if self.save_to_db:
       generation_id = self._save_generation(...)
   ```

6. **Return Results**
   ```python
   return {
       "generation_id": generation_id,
       "data": result.data,
       "success": result.success,
       ...
   }
   ```

### Schema Validation

**Why validate?**
- Catch errors early (before expensive API calls)
- Provide helpful error messages
- Ensure LLM receives well-formed schemas

**Validation Rules:**
1. Schema must be a non-empty dict
2. Each field must have a definition
3. Field definitions should have "type" key (warning if missing)

**Example:**

```python
# Valid
{"name": {"type": "string"}, "age": {"type": "integer"}}

# Invalid
{}  # Empty - raises error
{"name": None}  # None value - raises error
{"name": {"description": "oops"}}  # Missing "type" - logs warning
```

### Error Handling Strategy

**Three-Layer Approach:**

1. **Validation Errors** (User's fault)
   - Raise `SchemaValidationError`
   - Provide actionable error message
   - Don't save to database

2. **Backend Errors** (API/Network issues)
   - Catch and wrap exceptions
   - Save failed attempt to database (for debugging)
   - Return error result (don't crash)

3. **Database Errors** (Storage issues)
   - Log but don't fail generation
   - User still gets their data
   - Warning in logs

**Example:**

```python
try:
    result = self.backend.generate(...)
except Exception as e:
    error_msg = f"Backend failed: {str(e)}"
    logger.error(error_msg, exc_info=True)

    # Save failure for debugging
    gen_id = self._save_failed_generation(...)

    # Return error result (don't crash)
    return {
        "success": False,
        "error_message": error_msg,
        "data": [],
        ...
    }
```

### Progress Tracking

**Purpose:**
- Show user that something is happening
- Prevent "is it frozen?" anxiety
- Enable responsive UI (Streamlit progress bars)

**Implementation:**

```python
def show_progress(current, total):
    """Called during generation."""
    percent = (current / total) * 100
    print(f"Progress: {percent:.0f}%")

result = service.generate(
    schema=schema,
    num_records=100,
    on_progress=show_progress  # Pass callback
)
```

**When called:**
- Start: `on_progress(0, 100)` → 0%
- End: `on_progress(100, 100)` → 100%

In future phases, we'll add intermediate progress for batching.

## Testing Strategy

### Test Organization

```
TestSchemaValidation (6 tests)
├── Valid schemas (2 tests)
├── Invalid schemas (3 tests)
└── Warning cases (1 test)

TestGeneration (6 tests)
├── Without database (1 test)
├── With database (1 test)
├── Progress tracking (1 test)
├── Custom parameters (1 test)
├── Invalid inputs (1 test)
└── Failed attempts (1 test)

TestHistory (3 tests)
├── Get recent (1 test)
├── Filter by success (1 test)
└── Get by ID (1 test)

TestContextManager (1 test)
└── Resource cleanup

TestIntegration (1 test, skipped)
└── End-to-end with real API
```

### Mock vs Integration Tests

**Mock Tests (Unit Tests):**
- Fast (milliseconds)
- No API calls
- Use `Mock()` backend
- Test logic, not API

```python
mock_backend = Mock()
mock_backend.generate.return_value = GenerationResult(...)
service = GeneratorService(backend=mock_backend)
```

**Integration Tests:**
- Slower (seconds)
- Real API calls
- Require API key
- Test end-to-end flow

```python
@pytest.mark.skip(reason="Requires API key")
def test_end_to_end():
    backend = HuggingFaceAPIBackend(api_key=real_key)
    service = GeneratorService(backend=backend)
    result = service.generate(...)
```

### Running Tests

```bash
# All tests (fast, no API)
uv run pytest tests/test_generator.py -v

# With coverage
uv run pytest tests/test_generator.py --cov=synth_data.services

# Just one test
uv run pytest tests/test_generator.py::TestGeneration::test_generate_with_database -v

# Include integration tests (requires API key)
uv run pytest tests/test_generator.py -v --run-integration
```

## Design Patterns Used

### 1. Facade Pattern

**GeneratorService** provides a simple interface to a complex subsystem:

```python
# Without facade (complex)
backend = HuggingFaceAPIBackend(api_key)
db = DatabaseService()
result = backend.generate(schema, 10)
gen_id = db.save_generation(schema, result.data, ...)

# With facade (simple)
service = GeneratorService(backend, db)
result = service.generate(schema, 10)  # Handles everything
```

### 2. Dependency Injection

**Backend and database are injected**, not hardcoded:

```python
# Good: Testable, flexible
service = GeneratorService(backend=mock_backend, database=mock_db)

# Bad: Hardcoded, untestable
class GeneratorService:
    def __init__(self):
        self.backend = HuggingFaceAPIBackend()  # Hardcoded
```

### 3. Observer Pattern (Progress Tracking)

**Callbacks notify observers of progress:**

```python
def on_progress(current, total):
    """Observer gets notified"""
    print(f"{current}/{total}")

service.generate(..., on_progress=on_progress)
```

### 4. Context Manager

**Automatic resource cleanup:**

```python
with GeneratorService(backend, db) as service:
    result = service.generate(...)
# Database automatically closed
```

## Common Usage Patterns

### Pattern 1: Basic Generation (No Database)

**Use case:** Quick testing, one-off generation

```python
backend = HuggingFaceAPIBackend(api_key)
service = GeneratorService(backend, save_to_db=False)

result = service.generate(schema, num_records=10)
print(result["data"])
```

### Pattern 2: Persistent Generation (With Database)

**Use case:** Production, history tracking

```python
backend = HuggingFaceAPIBackend(api_key)
service = GeneratorService(backend, save_to_db=True)

result = service.generate(schema, num_records=100)
gen_id = result["generation_id"]

# Later: retrieve
generation = service.get_generation(gen_id)
```

### Pattern 3: Custom Parameters

**Use case:** Fine-tuning output quality/creativity

```python
from synth_data.backends.base import GenerationParams

params = GenerationParams(
    temperature=0.9,  # More creative
    max_tokens=2000,  # Longer responses
    top_p=0.95
)

result = service.generate(schema, 10, params=params)
```

### Pattern 4: Progress Tracking

**Use case:** Long-running generations, UI feedback

```python
def update_ui(current, total):
    progress_bar.update(current / total)

result = service.generate(
    schema,
    num_records=1000,
    on_progress=update_ui
)
```

### Pattern 5: Error Recovery

**Use case:** Robust production systems

```python
try:
    result = service.generate(schema, num_records)
    if result["success"]:
        process_data(result["data"])
    else:
        log_error(result["error_message"])
        retry_with_smaller_batch()
except SchemaValidationError as e:
    show_user_error(f"Invalid schema: {e}")
except Exception as e:
    log_critical_error(e)
    alert_admin()
```

## What We Learned

### 1. Service Layer Architecture

**Why have a service layer?**
- Encapsulates business logic
- Coordinates multiple components
- Provides clean API for UI layer
- Enables testing without UI

### 2. Validation Best Practices

**When to validate:**
- Early (before expensive operations)
- At system boundaries (user input)
- Not between internal components (trust your code)

**What to validate:**
- Data types and structure
- Required fields
- Value ranges (min/max)
- Cross-field dependencies (later phase)

### 3. Error Handling Philosophy

**Fail Fast:**
- Validation errors → raise immediately
- Don't waste API calls on invalid input

**Fail Gracefully:**
- API errors → catch, log, return error result
- Don't crash the whole system

**Fail Safely:**
- Database errors → log but continue
- User still gets their data

### 4. Progress Tracking Design

**Requirements:**
- Non-blocking (don't slow down generation)
- Flexible (works in CLI, GUI, web)
- Optional (not all callers need it)

**Solution: Callbacks**
- Caller provides function
- Service calls it at checkpoints
- Caller decides what to do (print, update UI, log)

### 5. Testing Strategies

**Test Pyramid:**
```
        ┌───────┐
        │  E2E  │  ← Few, slow, real API
        ├───────┤
        │ Integ │  ← Some, medium speed
        ├───────┤
        │ Unit  │  ← Many, fast, mocked
        └───────┘
```

**Our approach:**
- Many unit tests (fast, mocked)
- Few integration tests (skipped by default)
- Easy to run all tests before commit

## Next Steps

### Immediate (Tonight)

1. ~~Create GeneratorService~~ ✓
2. ~~Write comprehensive tests~~ ✓
3. ~~Create demo script~~ ✓

### Phase 1 Completion (Next Session)

4. **Export Service** (`services/export.py`)
   - CSV export
   - JSON/JSONL export
   - Streaming for large datasets

5. **Streamlit UI** (`ui/app.py`)
   - API key input
   - Schema editor
   - Generate button
   - Results display
   - History viewer

### Future Phases

**Phase 2:**
- Local quantized models
- Ollama backend
- Batch processing
- Quality metrics

**Phase 3:**
- Multi-page Streamlit app
- Quality visualizations
- Template system

**Phase 4:**
- HuggingFace Spaces deployment
- Multi-model comparison
- Advanced validation

## Files Created/Modified

### New Files
- `synth_data/services/generator.py` (400+ lines)
- `tests/test_generator.py` (300+ lines)
- `demo_generator.py` (200+ lines)
- `STEP_4_GENERATION_SERVICE.md` (this file)

### Modified Files
- `synth_data/services/__init__.py` (added exports)
- `tests/conftest.py` (added mock_database fixture)

## Resources

### Code References
- `synth_data/backends/base.py` - Backend interface
- `synth_data/backends/huggingface_api.py` - HF implementation
- `synth_data/database/service.py` - Database operations
- `synth_data/exceptions.py` - Custom exceptions

### Documentation
- `PLAN.md` - Overall project plan
- `README.md` - Setup and usage
- Architecture diagrams in PLAN.md

### External Resources
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Design Patterns](https://refactoring.guru/design-patterns)

## Questions & Answers

### Q: Why not use asyncio for async generation?

**A:** Phase 1 MVP uses synchronous code for simplicity. Async will be added in Phase 3 when we implement batching and parallel generation. This follows the principle: "Make it work, make it right, make it fast."

### Q: Why save failed generations to database?

**A:** Debugging and monitoring. When users report "it's not working", we can:
1. Check their recent failures in the database
2. See what schemas/settings caused problems
3. Track success rates over time
4. Identify patterns in failures

### Q: Why use callbacks instead of returning an iterator?

**A:** Callbacks are more flexible:
- Work in both sync and async code
- Don't require caller to poll
- Can be used for logging, UI updates, or ignored
- Easier to add intermediate checkpoints later

### Q: When should I use `save_to_db=False`?

**A:** Scenarios:
- Quick testing/experimentation
- Memory-constrained environments
- Generating throwaway data
- Using external storage (S3, etc.)

Default is `True` because history is valuable.

### Q: How do I add a new backend?

**A:** Three steps:
1. Create new class inheriting from `ModelBackend`
2. Implement `generate()` and `validate_connection()`
3. Pass to GeneratorService: `GeneratorService(backend=MyBackend())`

No changes needed to GeneratorService!

## Summary

In Step 4, we built the **orchestration layer** that ties together:
- Backend (API calls)
- Database (persistence)
- Validation (data quality)
- Progress tracking (user feedback)

This service provides a **clean, testable, extensible** interface for synthetic data generation. It follows **SOLID principles** and uses proven **design patterns** to ensure maintainability.

**Key Achievement:** Complete separation of concerns enables:
- Testing without API calls (fast unit tests)
- Swapping backends without code changes
- Adding features without breaking existing code

**Next:** Build the Streamlit UI that lets users interact with this service through a web interface.

---

**Generated:** 2026-01-24
**Author:** Claude Sonnet 4.5
**Course:** LLM Engineering (Ed Donner)
**Project:** Synthetic Data Generator v2
