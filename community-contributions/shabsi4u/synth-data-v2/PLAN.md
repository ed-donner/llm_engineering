# Business-Grade Synthetic Data Generator v2 - Implementation Plan

## Project Overview

Build a production-quality synthetic data generator that supports multiple model backends (local quantized, Ollama, HuggingFace API), handles large-scale generation (1000s of records), ensures data quality and coherence, and provides a professional Gradio UI suitable for business users. The system will be deployable both locally and on Google Colab.

## Business Requirements

**Quality Bar:**
- Enterprise reliability: comprehensive error handling, retries, validation, logging
- Professional UI/UX: suitable for non-technical business users
- Scalability: handle 1000s of records with batching, streaming, memory management
- Data quality: validation, coherence (field dependencies), diversity metrics
- **Generation history:** Database for tracking past generations, retrieving previous datasets

**Use Cases:**
- Testing/QA data generation
- ML training datasets
- Demo/mockup data
- Privacy-safe synthetic data

**Model Backends:**
- Local models (Llama 3.1, Mistral) with 4-bit quantization
- Ollama for easy deployment
- HuggingFace Inference API (free tier)
- Google Colab deployment support

**Deployment:**
- Python application (not notebook-based)
- Streamlit UI (compatible with HuggingFace Spaces)
- Local development and cloud deployment

## Architecture Summary

```
UI Layer (Streamlit)
    ↓
Application Layer (Orchestrator, TemplateManager, BatchController)
    ↓
Service Layer (ModelBackend abstraction, ValidationService, QualityService)
    ↓
Data Layer (Database, TemplateRepository, CacheManager, ExportManager)
    ↓
Database (SQLite/PostgreSQL) - Generation history, templates, quality metrics
```

### Core Components

1. **ModelBackend (Abstract)** - Interface for all model providers
   - LocalQuantizedBackend (4-bit Llama, Mistral, Qwen, Phi)
   - OllamaBackend
   - HuggingFaceAPIBackend
   - OpenAICompatibleBackend

2. **GeneratorOrchestrator** - Main coordinator
   - Request routing, batch management, retry logic, progress tracking

3. **BatchController** - Intelligent batching
   - Dynamic batch sizing, parallel execution, deduplication, progress streaming

4. **ValidationService** - Multi-layer validation
   - JSON schema, type checking, coherence (field dependencies), diversity scoring

5. **QualityService** - Data quality assurance
   - Duplicate detection, coherence scoring, diversity metrics, distribution analysis

6. **TemplateManager** - Enhanced template system
   - JSON schema templates, few-shot examples, dynamic prompts, context-aware generation

7. **DatabaseService** - Generation history and retrieval
   - Store generation metadata, schemas, quality metrics
   - Retrieve past generations
   - Search and filter capabilities
   - Analytics on generation patterns

## Implementation Phases

### Phase 1: Foundation & MVP (Week 1-2)

**Goal:** Working end-to-end system with single backend (HuggingFace API)

**Core Architecture Setup:**
1. Project structure and dependencies (Python package, not notebooks)
   ```
   community-contributions/shabsi4u/synth-data-v2/
   ├── synth_data/               # Main package
   │   ├── __init__.py
   │   ├── __main__.py           # Entry point: python -m synth_data
   │   ├── backends/
   │   │   ├── __init__.py
   │   │   ├── base.py           # ModelBackend ABC
   │   │   └── huggingface_api.py
   │   ├── core/
   │   │   ├── __init__.py
   │   │   └── orchestrator.py
   │   ├── database/
   │   │   ├── __init__.py
   │   │   ├── models.py         # SQLAlchemy models
   │   │   ├── service.py        # DatabaseService
   │   │   └── migrations/       # Alembic migrations
   │   ├── services/
   │   │   ├── __init__.py
   │   │   ├── validation.py
   │   │   └── export.py
   │   ├── templates/
   │   │   ├── __init__.py
   │   │   ├── manager.py
   │   │   └── schemas/          # JSON template files
   │   ├── ui/
   │   │   ├── __init__.py
   │   │   ├── app.py            # Streamlit app
   │   │   ├── pages/            # Multi-page app
   │   │   │   ├── 1_Generate.py
   │   │   │   ├── 2_History.py
   │   │   │   └── 3_Quality.py
   │   │   └── components.py     # Reusable UI components
   │   └── utils/
   │       ├── __init__.py
   │       └── json_parser.py
   ├── tests/
   │   ├── __init__.py
   │   ├── unit/
   │   └── integration/
   ├── .streamlit/
   │   └── config.toml           # Streamlit config
   ├── requirements.txt
   ├── pyproject.toml
   ├── README.md
   └── .env.example
   ```

2. **ModelBackend Interface** (backends/base.py)
   ```python
   class ModelBackend(ABC):
       @abstractmethod
       async def generate(self, prompt: str, params: GenerationParams) -> GenerationResult
       @abstractmethod
       def supports_streaming(self) -> bool
       @abstractmethod
       def get_capabilities(self) -> ModelCapabilities
   ```

3. **HuggingFaceAPIBackend** (backends/huggingface_api.py)
   - Reuse v1's HFClient pattern with OpenAI compatibility
   - Add retry logic with tenacity
   - Add rate limiting awareness

4. **Database Setup** (database/)
   - SQLAlchemy models:
     ```python
     class Generation(Base):
         id: UUID primary key
         created_at: DateTime
         schema_json: JSON
         model_backend: String
         num_records: Integer
         quality_score: Float
         status: Enum (pending, completed, failed)
         error_message: Text (nullable)

     class GeneratedDataset(Base):
         id: UUID primary key
         generation_id: FK(Generation)
         data_json: JSON (or file path for large datasets)
         export_formats: JSON (list of available formats)

     class Template(Base):
         id: UUID primary key
         name: String
         schema_json: JSON
         examples: JSON
         created_at: DateTime
         use_count: Integer
     ```
   - SQLite for local development
   - PostgreSQL for production/HuggingFace Spaces
   - DatabaseService for CRUD operations

5. **Basic Validation** (services/validation.py)
   - JSON schema validation using jsonschema library
   - Type checking with pydantic
   - Basic duplicate detection

6. **Export Manager** (services/export.py)
   - CSV, JSON, JSONL formats
   - Streaming export for large datasets (borrowed from Juan's pattern)
   - Save export metadata to database

7. **Simple Streamlit UI** (ui/app.py)
   - Main page: schema input → generate → preview → export
   - Sidebar: model selection, settings
   - Progress bar with Streamlit's st.progress()
   - Error display with st.error()
   - Session state management for app state

**Learning Focus:**
- Understand abstract base classes and dependency injection
- Learn pydantic for data validation
- SQLAlchemy ORM and database design
- Streamlit basics: components, session state, pages

**Success Criteria:**
- Generate 100 records from custom schema via HF API
- Validate against JSON schema
- Export to CSV/JSON
- Handle API errors gracefully
- Unit tests pass

---

### Phase 2: Multi-Backend & Quality System (Week 3-4)

**Goal:** Support local quantized models, Ollama, and implement quality assurance

**Local Model Support:**
1. **LocalQuantizedBackend** (backends/local_quantized.py)
   - 4-bit quantization setup (BitsAndBytesConfig)
   - Model loading with transformers
   - GPU memory management
   - Based on Week 3 course patterns:
     ```python
     quant_config = BitsAndBytesConfig(
         load_in_4bit=True,
         bnb_4bit_use_double_quant=True,
         bnb_4bit_compute_dtype=torch.bfloat16,
         bnb_4bit_quant_type="nf4"
     )
     model = AutoModelForCausalLM.from_pretrained(
         model_id,
         quantization_config=quant_config,
         device_map="auto"
     )
     ```

2. **OllamaBackend** (backends/ollama.py)
   - HTTP client to Ollama API
   - Model detection and listing
   - Simpler alternative to local quantized

3. **Batch Processing** (core/batch_controller.py)
   - Dynamic batch sizing algorithm (from Juan's data_generation.py):
     ```python
     # Estimate tokens
     prompt_tokens = len(prompt_sample) // 4
     tokens_per_row = estimate_from_reference(reference_data)

     # Calculate batch size
     available_tokens = model_max_tokens - prompt_tokens - buffer
     batch_size = max(1, available_tokens // tokens_per_row)

     # Apply constraints (memory, rate limits)
     ```
   - Progress tracking with callbacks
   - Deduplication with hashing (hash_row pattern from Juan)

4. **Quality Service** (services/quality.py)
   - Diversity metrics:
     ```python
     def calculate_simpson_index(data: List[Dict]) -> float
     def calculate_shannon_entropy(data: List[Dict]) -> float
     def detect_near_duplicates(data: List[Dict], threshold: float) -> List[Tuple]
     ```
   - Coherence validation:
     ```python
     class CoherenceValidator:
         def validate(self, record: Dict, rules: List[DependencyRule]) -> CoherenceResult
     ```
   - Quality scoring (0-100 scale)

5. **Enhanced UI** (ui/pages/)
   - Multi-page Streamlit app
   - Page 1 - Generate: Model selection, schema input, generation
   - Page 2 - History: Browse past generations, search/filter
   - Page 3 - Quality: Quality reports and visualizations
   - Batch size configuration
   - Quality report display (inspired by Juan's evaluator)

**Learning Focus:**
- 4-bit quantization mechanics and memory optimization
- Batch processing strategies and token estimation
- Diversity metrics (Simpson's Index, Shannon Entropy)
- Field dependency validation patterns

**Success Criteria:**
- Generate 1000 records with local Llama 3.1 8B (4-bit)
- Batch processing with progress tracking
- Quality score > 85/100
- Duplicate rate < 2%
- Memory usage < 8GB

---

### Phase 3: Scalability & Professional Polish (Week 5-6)

**Goal:** Handle 10,000+ records, advanced quality metrics, production-grade UI

**Scalability Enhancements:**
1. **Async Generation** (core/orchestrator.py)
   - Async/await for API backends
   - Concurrent batch processing where supported
   - Memory-efficient streaming

2. **Advanced Export** (services/export.py)
   - Parquet, Excel formats
   - Streaming exports for large datasets
   - Train/validation split option
   - Metadata inclusion (config, timestamp, quality scores)

3. **Quality Evaluation** (services/evaluator.py)
   - Statistical comparison (mean, std, distribution overlap) - from Juan's evaluator.py
   - Visualization generation (histograms, boxplots)
   - Reference data comparison:
     ```python
     def compare_distributions(reference_df, generated_df) -> ComparisonReport
     def create_visualizations(reference_df, generated_df) -> Dict[str, List[Image]]
     ```

4. **Template System** (templates/)
   - Pre-built templates with JSON schemas
   - Few-shot example management
   - Template versioning
   - Examples: user_profile, customer_data, transaction_history, product_catalog

5. **Professional Streamlit UI**
   - Multi-page app with sidebar navigation:
     - Page 1 - Generate: Configuration, model selection, schema input, generation
     - Page 2 - History: Browse past generations with filters
       - Search by schema, model, date range
       - View generation details
       - Re-download exports
       - Delete old generations
     - Page 3 - Quality: Quality reports with interactive visualizations
       - Distribution comparisons (Plotly charts)
       - Diversity metrics dashboard
       - Quality score trends over time
     - Page 4 - Templates: Browse, create, edit templates
   - Error messages with actionable suggestions
   - Loading states with st.spinner()
   - Responsive layout with Streamlit columns
   - Custom CSS for professional look

6. **Error Handling & Logging**
   - Retry strategies with exponential backoff
   - Circuit breaker patterns
   - Structured logging (JSON format)
   - User-friendly error messages

**Learning Focus:**
- Async Python patterns and concurrency
- Statistical analysis and visualization with matplotlib/seaborn
- Production logging best practices
- Professional UI/UX design patterns

**Success Criteria:**
- Generate 10,000 records efficiently (< 3 hours with local model)
- Memory-efficient processing (no OOM errors)
- Quality reports with visualizations
- Professional UI that non-technical users can navigate
- Comprehensive error handling

---

### Phase 4: Google Colab & Advanced Features (Week 7-8)

**Goal:** Colab deployment, advanced coherence, enterprise features

**HuggingFace Spaces Deployment:**
1. **Spaces Configuration** (README.md with frontmatter)
   ```yaml
   ---
   title: Synthetic Data Generator v2
   emoji: 🎲
   colorFrom: blue
   colorTo: purple
   sdk: streamlit
   sdk_version: 1.31.0
   app_file: synth_data/ui/app.py
   pinned: false
   ---
   ```

2. **Streamlit on HuggingFace Spaces**
   - Streamlit is fully supported on HF Spaces
   - Automatic deployment from Git repo
   - Public URL for sharing
   - GPU hardware options available
   - Requirements.txt for dependencies

3. **Cloud Database** (for Spaces deployment)
   - Use PostgreSQL with HF Secrets for connection string
   - Or SQLite with persistent storage
   - Migration scripts for schema setup

4. **Environment Variables**
   - HF Secrets for API keys
   - Database connection strings
   - Model cache paths

**Advanced Features:**
1. **Multi-Model Comparison** (core/comparison.py)
   - Generate same dataset with different models
   - Side-by-side quality comparison
   - Cost/speed/quality trade-off analysis

2. **Interactive Template Builder** (ui/template_builder.py)
   - Visual schema creation
   - Field dependency configuration
   - Example data input
   - Save custom templates

3. **Advanced Coherence** (utils/coherence_validator.py)
   - Complex dependency rules:
     ```python
     DependencyRule(
         field="phone_number",
         depends_on=["country"],
         validator=lambda r: r["phone_number"].startswith(COUNTRY_CODES[r["country"]]),
         auto_fix=True  # Attempt automatic correction
     )
     ```
   - Auto-fix capabilities
   - Contextual generation (like ranskills' coherent generator)

4. **SQL DDL to Schema Converter** (utils/ddl_parser.py)
   - Parse CREATE TABLE statements
   - Generate JSON schema
   - Map SQL types to JSON types

5. **Documentation & Examples**
   - Complete API reference
   - Tutorial notebooks for each use case
   - Best practices guide
   - Performance optimization tips

**Learning Focus:**
- Google Colab deployment patterns
- Complex validation logic and auto-correction
- SQL parsing and schema transformation
- Documentation writing for technical and non-technical audiences

**Success Criteria:**
- Successfully deploy to Google Colab with public link
- Generate datasets from SQL DDL
- Multi-model comparison working
- Interactive template builder functional
- Complete documentation suite

---

## Critical Files & References

**Files to Study:**
1. `/Users/shabs/workspace/llm_engineering/community-contributions/shabsi4u/synthetic-data-generator/cursor_synth/core.py`
   - v1 architecture patterns (TemplateRegistry, Generator, Validator)

2. `/Users/shabs/workspace/llm_engineering/week3/community-contributions/juan_synthetic_data/src/data_generation.py`
   - Dynamic batching, token estimation, deduplication

3. `/Users/shabs/workspace/llm_engineering/week3/community-contributions/juan_synthetic_data/src/evaluator.py`
   - Quality evaluation, distribution comparison, visualization

4. `/Users/shabs/workspace/llm_engineering/community-contributions/shabsi4u/synthetic-data-generator/cursor_synth/utils.py`
   - Robust JSON extraction with fallbacks

5. `/Users/shabs/workspace/llm_engineering/week3/community-contributions/ranskills-week3-coherent-data-generator.ipynb`
   - 4-bit quantization setup, coherent generation, Gradio UI

**Files to Create:**
- All files in the structure shown in Phase 1
- Expand incrementally in each phase

---

## Technology Stack

**Core Dependencies:**
```python
# UI
streamlit >= 1.31.0
plotly >= 5.18.0  # Interactive charts for Streamlit

# Database
sqlalchemy >= 2.0.0
alembic >= 1.13.0  # Database migrations
psycopg2-binary >= 2.9.9  # PostgreSQL adapter (optional)

# Models
transformers >= 4.40.0
torch >= 2.0.0
bitsandbytes >= 0.43.0
accelerate >= 0.30.0
openai >= 1.0.0

# Data & Validation
pandas >= 2.0.0
pyarrow >= 15.0.0
jsonschema >= 4.19.0
pydantic >= 2.0.0

# Export
openpyxl >= 3.1.0

# Visualization
matplotlib >= 3.7.0
seaborn >= 0.12.0

# Utilities
python-dotenv >= 1.0.0
httpx >= 0.24.0
tenacity >= 8.0.0
pyyaml >= 6.0.0

# Testing
pytest >= 7.4.0
pytest-asyncio >= 0.21.0
pytest-cov >= 4.1.0
```

---

## Key Design Patterns

1. **Strategy Pattern** - Swappable model backends
2. **Pipeline Pattern** - Validation chain
3. **Observer Pattern** - Progress tracking
4. **Factory Pattern** - Backend creation
5. **Builder Pattern** - Prompt construction

---

## Testing Strategy

**Unit Tests:**
- All service classes (90%+ coverage)
- Validation logic (100% coverage)
- Export functionality
- Model backend interfaces

**Integration Tests:**
- End-to-end generation with each backend
- Batch processing with 1000+ records
- Export to all formats
- Quality validation pipeline

**Performance Tests:**
- Generation speed benchmarks
- Memory usage profiling
- Token throughput measurement

---

## Learning Approach

**Incremental Build with Detailed Explanations:**

For each component:
1. **Explain the Why** - Business need, architectural decision
2. **Show the Pattern** - Design pattern being used, reference examples
3. **Implement Together** - Build the component step by step
4. **Test & Validate** - Write tests, verify functionality
5. **Reflect & Refine** - Discuss trade-offs, optimizations

**Key Learning Moments:**
- Phase 1: Abstract interfaces, dependency injection, pydantic, SQLAlchemy ORM, Streamlit basics
- Phase 2: Quantization mechanics, batching algorithms, diversity metrics, database queries
- Phase 3: Async programming, statistical analysis, multi-page Streamlit apps, Plotly visualizations
- Phase 4: HuggingFace Spaces deployment, PostgreSQL migrations, advanced validation, SQL parsing

---

## Success Metrics

**Phase 1 MVP:**
- ✅ Generate 100 records via HF API
- ✅ JSON schema validation
- ✅ CSV/JSON export
- ✅ Basic error handling

**Phase 2 Multi-Backend:**
- ✅ Support 3+ backends
- ✅ Generate 1000 records with batching
- ✅ Quality score > 85
- ✅ Duplicate rate < 2%

**Phase 3 Production:**
- ✅ Generate 10,000+ records
- ✅ Professional UI/UX
- ✅ Quality reports with viz
- ✅ Comprehensive error handling

**Phase 4 Advanced:**
- ✅ HuggingFace Spaces deployment
- ✅ Multi-model comparison
- ✅ Interactive template builder
- ✅ Complete documentation

---

## Additional Features (Database-Driven)

**Generation History:**
- Store all generations with metadata (schema, model, settings, timestamp)
- Search and filter past generations
- View quality trends over time
- Re-export previous datasets in different formats
- Delete old generations to manage storage

**Analytics Dashboard:**
- Most used templates
- Model performance comparison (quality scores over time)
- Generation volume trends
- Token usage and cost tracking

**Template Library:**
- Save custom templates to database
- Share templates across generations
- Version templates
- Track template usage and effectiveness

---

## Next Steps

1. **Set up project structure** in `community-contributions/shabsi4u/synth-data-v2/`
2. **Create Python package structure** (not notebooks)
3. **Initialize SQLite database** with SQLAlchemy models
4. **Create basic Streamlit app** with single page
5. **Implement Phase 1 MVP** - start with base.py and huggingface_api.py
6. **Build incrementally** with tests for each component
7. **Learn and document** design decisions at each step

---

## HuggingFace Spaces Compatibility

**Streamlit on HF Spaces:**
- ✅ Officially supported SDK
- ✅ Automatic builds from requirements.txt
- ✅ GPU hardware available (for local models)
- ✅ Persistent storage options
- ✅ Secrets management for API keys
- ✅ Free tier available (CPU-only)
- ✅ Custom domains and branding

**Deployment Workflow:**
1. Push code to HF Spaces Git repo
2. Add README with SDK configuration
3. Configure secrets (API keys, DB connection)
4. Select hardware (CPU/GPU)
5. Automatic deployment and public URL

**Storage Options:**
- SQLite database file (persistent across restarts)
- PostgreSQL via connection string in secrets
- HF Datasets for large dataset storage

---

## API Key Security

**CRITICAL: No hardcoded API keys in code**

**Hybrid Approach: .env for Local + User Input for Hosted**

**Local Development (.env file):**
```bash
# .env (add to .gitignore!)
HUGGINGFACE_API_KEY=hf_xxxxx
OPENAI_API_KEY=sk-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**Hosted/External Users (Streamlit input):**
```python
import os
from dotenv import load_dotenv

# Try loading from .env first (local dev)
load_dotenv()
default_key = os.getenv("HUGGINGFACE_API_KEY", "")

# If not in .env, prompt user (hosted deployment)
api_key = st.text_input(
    "API Key (leave blank if using local models)",
    value=default_key,
    type="password" if not default_key else "default",
    help="Enter your API key, or leave blank for local/Ollama models"
)

# Store in session state
if api_key:
    st.session_state.api_key = api_key
```

**Security Best Practices:**
- ❌ Never commit API keys to Git (add .env to .gitignore)
- ❌ Never store API keys in database
- ❌ Never log API keys
- ✅ Local dev: Use .env file (convenient, not committed)
- ✅ Hosted: User provides via password input
- ✅ Store only in st.session_state (memory, not persisted)
- ✅ Use HF Spaces Secrets for production deployment
- ✅ Blank/empty key = local models only

**Implementation:**
```python
class ModelBackend:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key else None

    def _get_client(self):
        if not self.api_key:
            raise ValueError("API key required for this backend")
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
```

**.env.example (commit this for reference):**
```bash
# Copy to .env and add your actual keys

# HuggingFace (for HF Inference API)
HUGGINGFACE_API_KEY=your_key_here

# OpenAI (optional, for GPT models)
OPENAI_API_KEY=your_key_here

# Anthropic (optional, for Claude)
ANTHROPIC_API_KEY=your_key_here
```

---

## REVISED Timeline: Tonight's MVP

**Goal: Working demo in 4-6 hours**

### Tonight's Scope (Minimal Viable Product)

**Phase 1 ONLY - Absolute Essentials:**

1. **Project Setup** (30 min)
   - Create directory structure
   - requirements.txt with minimal dependencies
   - Basic Streamlit app skeleton

2. **Single Backend - HuggingFace API** (1 hour)
   - ModelBackend interface
   - HuggingFaceAPIBackend implementation
   - User provides API key via Streamlit input

3. **Basic Generation** (1.5 hours)
   - Simple schema input (JSON text area)
   - Generate button
   - Display results in table
   - NO batching, NO quality metrics, NO validation yet

4. **Minimal Database** (1 hour)
   - SQLite with 1 table: Generation
   - Save: timestamp, schema, num_records, data_json
   - Display history in expander

5. **Basic Export** (30 min)
   - CSV download only
   - st.download_button()

6. **Simple UI** (1 hour)
   - Single page Streamlit app
   - Sections: API Key → Schema → Generate → Results → History
   - No multi-page, no charts, minimal styling

**Total: ~5.5 hours = Doable tonight!**

**NOT Included in Tonight's MVP:**
- ❌ Local quantized models (too complex for tonight)
- ❌ Ollama integration
- ❌ Batch processing
- ❌ Quality metrics
- ❌ Coherence validation
- ❌ Multiple export formats
- ❌ Visualizations
- ❌ Multi-page app
- ❌ Template system

**Can Add Later (Future Sessions):**
- Phase 2: Local models + Ollama
- Phase 3: Quality metrics + batching
- Phase 4: Multi-page UI + visualizations
- Phase 5: HF Spaces deployment

---

## Tonight's Implementation Order

1. **Setup** (30 min)
   ```bash
   mkdir -p synth_data/{backends,database,ui}
   touch requirements.txt pyproject.toml
   ```

2. **Dependencies** (requirements.txt)
   ```
   streamlit
   openai  # HF-compatible client
   sqlalchemy
   pandas
   python-dotenv
   ```

3. **Database Model** (database/models.py)
   ```python
   class Generation(Base):
       id = Column(Integer, primary_key=True)
       created_at = Column(DateTime, default=datetime.utcnow)
       schema_json = Column(JSON)
       num_records = Column(Integer)
       data_json = Column(JSON)  # Store directly for MVP
   ```

4. **Backend Interface** (backends/base.py + backends/huggingface_api.py)
   - Accept user API key in __init__
   - Simple generate() method

5. **Streamlit App** (ui/app.py)
   ```python
   st.title("Synthetic Data Generator MVP")

   # API Key Input
   api_key = st.text_input("API Key", type="password")

   # Schema Input
   schema = st.text_area("Schema (JSON)")
   num_records = st.number_input("Records", 1, 100, 10)

   # Generate
   if st.button("Generate"):
       # Parse schema, call backend, save to DB, display

   # History
   with st.expander("Generation History"):
       # Query DB, display table
   ```

6. **Test Run**
   ```bash
   streamlit run synth_data/ui/app.py
   ```

---

## Success Criteria for Tonight

✅ User can input their own API key
✅ User can define simple schema (JSON)
✅ Generate 10-50 synthetic records
✅ View results in table
✅ Download as CSV
✅ See past generations in history
✅ No API keys in code/Git
✅ Works locally with `streamlit run`

**Stretch Goals (if time permits):**
- Basic error handling
- Input validation
- Pretty formatting
- README with setup instructions

---

## Code Best Practices & Standards

### Project Organization

**Directory Structure:**
```
synth-data-v2/
├── synth_data/              # Main package
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # CLI entry point
│   ├── config.py            # Configuration management
│   ├── backends/            # Model backend implementations
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract base class
│   │   └── huggingface_api.py
│   ├── database/            # Database layer
│   │   ├── __init__.py
│   │   ├── models.py        # SQLAlchemy models
│   │   └── service.py       # Database operations
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── generator.py     # Core generation logic
│   │   └── export.py        # Export functionality
│   ├── ui/                  # Streamlit UI
│   │   ├── __init__.py
│   │   └── app.py           # Main Streamlit app
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── helpers.py
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_backends.py
│   └── test_database.py
├── .env.example             # Template for environment variables
├── .gitignore              # Git ignore patterns
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata
└── README.md               # Project documentation
```

### Naming Conventions

**Files & Modules:**
- Lowercase with underscores: `model_backend.py`, `database_service.py`
- Clear, descriptive names indicating purpose

**Classes:**
- PascalCase: `ModelBackend`, `GenerationService`, `DatabaseModel`
- Nouns that represent entities/objects

**Functions & Methods:**
- snake_case: `generate_data()`, `save_to_database()`, `export_csv()`
- Verbs that describe actions

**Constants:**
- UPPERCASE with underscores: `MAX_RETRIES`, `DEFAULT_TEMPERATURE`, `API_TIMEOUT`

**Private Members:**
- Single underscore prefix: `_internal_method()`, `_parse_response()`

### Code Documentation

**Module Docstrings:**
```python
"""
Backend implementations for synthetic data generation.

This module contains abstract base classes and concrete implementations
for various LLM backends (HuggingFace, OpenAI, Ollama, etc.).
"""
```

**Class Docstrings:**
```python
class ModelBackend(ABC):
    """
    Abstract base class for LLM backend implementations.

    Provides interface for generating synthetic data using various
    LLM providers. Subclasses must implement generate() method.

    Attributes:
        api_key: Optional API key for cloud providers
        model_id: Identifier for the specific model to use
    """
```

**Function Docstrings (Google Style):**
```python
def generate_data(schema: dict, num_records: int, api_key: str) -> pd.DataFrame:
    """
    Generate synthetic data based on provided schema.

    Args:
        schema: JSON schema defining the data structure
        num_records: Number of records to generate
        api_key: API key for the LLM provider

    Returns:
        DataFrame containing the generated synthetic data

    Raises:
        ValueError: If schema is invalid or num_records < 1
        APIError: If the LLM API call fails

    Example:
        >>> schema = {"name": {"type": "string"}, "age": {"type": "integer"}}
        >>> df = generate_data(schema, 10, "hf_xxx")
        >>> len(df)
        10
    """
```

### Type Hints

**Always use type hints:**
```python
from typing import Optional, List, Dict, Any
from datetime import datetime

def save_generation(
    schema: Dict[str, Any],
    data: pd.DataFrame,
    timestamp: datetime,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Save generation to database and return ID."""
    pass
```

### Error Handling

**Specific Exceptions:**
```python
class SynthDataError(Exception):
    """Base exception for synthetic data generator."""
    pass

class APIKeyError(SynthDataError):
    """Raised when API key is missing or invalid."""
    pass

class SchemaValidationError(SynthDataError):
    """Raised when schema validation fails."""
    pass

class GenerationError(SynthDataError):
    """Raised when data generation fails."""
    pass
```

**Try/Except Patterns:**
```python
def generate_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Generate with automatic retry on failure."""
    for attempt in range(max_retries):
        try:
            return self._call_api(prompt)
        except APIError as e:
            if attempt == max_retries - 1:
                raise GenerationError(f"Failed after {max_retries} attempts") from e
            logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
```

**User-Friendly Error Messages:**
```python
try:
    data = generate_data(schema, num_records, api_key)
except APIKeyError:
    st.error("❌ Invalid API key. Please check your credentials.")
except SchemaValidationError as e:
    st.error(f"❌ Schema validation failed: {e}")
    st.info("💡 Tip: Ensure your schema uses valid JSON Schema format")
except GenerationError as e:
    st.error(f"❌ Generation failed: {e}")
    st.info("💡 Try reducing the number of records or simplifying the schema")
```

### Logging

**Structured Logging:**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('synth_data.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage
logger.info("Starting generation", extra={
    "num_records": num_records,
    "model": model_id,
    "schema_fields": len(schema)
})

logger.error("Generation failed", extra={
    "error": str(e),
    "schema": schema
}, exc_info=True)
```

**Log Levels:**
- `DEBUG`: Detailed info for debugging (not in production)
- `INFO`: General informational messages
- `WARNING`: Warning messages (recoverable issues)
- `ERROR`: Error messages (operation failed)
- `CRITICAL`: Critical errors (system failure)

### Configuration Management

**config.py:**
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Keys (loaded from .env)
    huggingface_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Database
    database_url: str = "sqlite:///synth_data.db"

    # Generation Defaults
    default_temperature: float = 0.7
    default_max_tokens: int = 2048
    max_retries: int = 3

    # UI
    app_title: str = "Synthetic Data Generator v2"
    page_icon: str = "🎲"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance
settings = Settings()
```

**Usage:**
```python
from synth_data.config import settings

backend = HuggingFaceAPIBackend(
    api_key=settings.huggingface_api_key,
    temperature=settings.default_temperature
)
```

### Testing Best Practices

**Test Structure:**
```python
import pytest
from synth_data.backends import HuggingFaceAPIBackend

class TestHuggingFaceBackend:
    """Test suite for HuggingFace API backend."""

    @pytest.fixture
    def backend(self):
        """Fixture providing a configured backend instance."""
        return HuggingFaceAPIBackend(api_key="test_key")

    def test_init_with_api_key(self):
        """Test backend initialization with API key."""
        backend = HuggingFaceAPIBackend(api_key="test")
        assert backend.api_key == "test"

    def test_init_without_api_key_raises(self):
        """Test that missing API key raises error."""
        with pytest.raises(APIKeyError):
            HuggingFaceAPIBackend().generate("prompt")

    @pytest.mark.integration
    def test_generate_real_api(self, backend):
        """Integration test with real API (requires key)."""
        result = backend.generate("Generate test data")
        assert isinstance(result, str)
```

**Run Tests:**
```bash
# All tests
pytest

# Unit tests only
pytest -m "not integration"

# With coverage
pytest --cov=synth_data --cov-report=html
```

### Git Workflow

**.gitignore:**
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Streamlit
.streamlit/secrets.toml
```

**Commit Messages:**
```bash
# Format: <type>: <subject>

# Types:
# feat: New feature
# fix: Bug fix
# docs: Documentation
# style: Formatting
# refactor: Code restructuring
# test: Adding tests
# chore: Maintenance

# Examples:
git commit -m "feat: add HuggingFace API backend"
git commit -m "fix: handle empty API key gracefully"
git commit -m "docs: add API key setup instructions"
git commit -m "refactor: extract validation logic to service"
```

**Branch Strategy (for later phases):**
```bash
# Main branch
main

# Feature branches
git checkout -b feat/ollama-backend
git checkout -b fix/csv-export-bug

# Merge via PR after testing
```

### Code Quality Tools

**Linting & Formatting:**
```bash
# Install
pip install black ruff mypy

# Format code
black synth_data/

# Lint
ruff check synth_data/

# Type checking
mypy synth_data/
```

**Pre-commit Hooks (optional):**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
```

### Development Setup Instructions

**README.md Template:**
````markdown
# Synthetic Data Generator v2

Business-grade synthetic data generation using LLMs.

## Quick Start

### Prerequisites
- Python 3.10+
- pip or uv

### Installation

```bash
# Clone repository
git clone <repo-url>
cd synth-data-v2

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### Run Application

```bash
# Start Streamlit app
streamlit run synth_data/ui/app.py

# Or via package
python -m synth_data
```

## Project Structure

```
synth_data/
├── backends/     # LLM backend implementations
├── database/     # SQLAlchemy models and services
├── services/     # Business logic
├── ui/           # Streamlit interface
└── utils/        # Helper functions
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black synth_data/
ruff check synth_data/
```

### Adding a New Backend

1. Create file in `backends/`
2. Inherit from `ModelBackend`
3. Implement `generate()` method
4. Add tests
5. Update UI model selector

## License

MIT
````

### Performance Considerations

**For Tonight's MVP:**
```python
# Simple, synchronous implementation
def generate_data(schema: dict, num_records: int) -> pd.DataFrame:
    """Generate data synchronously (good for < 100 records)."""
    records = []
    for i in range(num_records):
        record = self._generate_single_record(schema)
        records.append(record)
    return pd.DataFrame(records)
```

**For Future Optimization:**
```python
# Async batch processing (for 1000+ records)
async def generate_data_async(schema: dict, num_records: int) -> pd.DataFrame:
    """Generate data asynchronously in batches."""
    batch_size = 10
    tasks = []
    for i in range(0, num_records, batch_size):
        batch = min(batch_size, num_records - i)
        tasks.append(self._generate_batch_async(schema, batch))
    results = await asyncio.gather(*tasks)
    return pd.concat(results)
```

### Security Checklist

- [ ] `.env` in `.gitignore`
- [ ] No API keys in code
- [ ] No API keys in database
- [ ] API keys in session state only
- [ ] Input validation for schemas
- [ ] SQL injection prevention (SQLAlchemy ORM handles this)
- [ ] XSS prevention in Streamlit (Streamlit handles this)
- [ ] Rate limiting for API calls (future)

---

## Tonight's Implementation Checklist

### Setup (30 min)
- [ ] Create project directory structure
- [ ] Initialize git repository
- [ ] Create requirements.txt
- [ ] Create .env.example
- [ ] Add .gitignore
- [ ] Create README.md skeleton

### Backend (1 hour)
- [ ] Create backends/base.py with ModelBackend ABC
- [ ] Create backends/huggingface_api.py
- [ ] Add type hints and docstrings
- [ ] Basic error handling

### Database (1 hour)
- [ ] Create database/models.py with Generation model
- [ ] Create database/service.py with CRUD operations
- [ ] Initialize SQLite database
- [ ] Test database operations

### Generation (1.5 hours)
- [ ] Create services/generator.py
- [ ] Implement schema parsing
- [ ] Implement generation logic
- [ ] Add logging

### Export (30 min)
- [ ] Create services/export.py
- [ ] Implement CSV export
- [ ] Test export functionality

### UI (1 hour)
- [ ] Create ui/app.py
- [ ] API key input with .env fallback
- [ ] Schema input
- [ ] Generate button with progress
- [ ] Results display
- [ ] History expander
- [ ] Download button

### Testing & Polish (30 min)
- [ ] Write unit tests for backends
- [ ] Write unit tests for database operations
- [ ] Manual testing of UI flow
- [ ] Error handling improvements
- [ ] README updates
- [ ] Code cleanup

---

## Learning Approach: Manual Approval Recommended

**For Maximum Learning:**
- ✅ **Manual approval** for each component
- Review code before I write it
- Ask questions about design decisions
- Understand trade-offs and alternatives
- Modify/improve suggestions

**Workflow:**
1. I explain the component we're building
2. I show the code structure and key patterns
3. You approve or ask for modifications
4. I implement with detailed comments
5. We test together and discuss

**Why Manual vs Auto:**
- Auto-accept: Faster, but less learning
- Manual: Slower, but you understand every decision
- Recommended: Manual for core components, auto for boilerplate

---

## Code Style: No Emojis in Code

**Emojis Policy:**
- ❌ No emojis in code, comments, or docstrings
- ❌ No emojis in log messages
- ❌ No emojis in error messages (code-level)
- ✅ OK in Streamlit UI (user-facing messages only)
- ✅ OK in README for visual appeal

**Examples:**

**Bad (code):**
```python
# 🚀 Generate data with retry logic
def generate_with_retry():
    logger.info("✅ Generation successful")
```

**Good (code):**
```python
# Generate data with automatic retry on failure
def generate_with_retry():
    logger.info("Generation completed successfully")
```

**OK (Streamlit UI):**
```python
st.success("✅ Generation completed successfully")
st.error("❌ API key is invalid")
st.info("💡 Tip: Use smaller batch sizes for faster results")
```

---

## REST API: FastAPI Integration (Optional Phase)

**Question: Should we add REST API alongside Streamlit?**

**Option A: Streamlit Only (Tonight's MVP)**
- Simpler, faster to build
- Good for single-user local use
- Streamlit handles authentication, sessions
- Perfect for prototyping and demos

**Option B: Streamlit + FastAPI (Future Enhancement)**
- More complex, takes longer
- Enables programmatic access
- Better for integrations
- Production-ready API

**Recommended: Start with Streamlit, add FastAPI later**

### If We Add FastAPI (Future Phase):

**Architecture:**
```
User → Streamlit UI → Core Services ← FastAPI REST API → External Clients
```

**Project Structure (with API):**
```
synth_data/
├── api/                 # FastAPI REST API
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── generate.py  # POST /generate
│   │   └── history.py   # GET /history
│   ├── schemas.py       # Pydantic request/response models
│   └── dependencies.py  # Auth, rate limiting
├── ui/                  # Streamlit UI
│   └── app.py
└── services/            # Shared business logic
    └── generator.py     # Used by both UI and API
```

**FastAPI Example:**
```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Synthetic Data Generator API")

class GenerateRequest(BaseModel):
    """Request schema for data generation."""
    schema: dict
    num_records: int
    api_key: str
    temperature: Optional[float] = 0.7

class GenerateResponse(BaseModel):
    """Response schema for data generation."""
    generation_id: str
    num_records: int
    data: list[dict]
    quality_score: Optional[float] = None

@app.post("/generate", response_model=GenerateResponse)
async def generate_data(request: GenerateRequest):
    """
    Generate synthetic data based on provided schema.

    Example:
        POST /generate
        {
            "schema": {"name": {"type": "string"}},
            "num_records": 10,
            "api_key": "hf_xxx"
        }
    """
    try:
        # Use shared service layer
        service = GeneratorService(api_key=request.api_key)
        result = await service.generate(
            schema=request.schema,
            num_records=request.num_records
        )
        return GenerateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history(limit: int = 10):
    """Get generation history."""
    db = DatabaseService()
    history = db.get_recent_generations(limit=limit)
    return {"generations": history}
```

**Benefits of FastAPI:**
- Automatic OpenAPI/Swagger docs
- Type validation with Pydantic
- Async support for high performance
- Easy authentication middleware
- Rate limiting
- CORS support
- Production-ready

**When to Add FastAPI:**
- Need programmatic access (CLI tools, integrations)
- Building multi-user service
- Need authentication/authorization
- Want to expose as public API
- Need rate limiting and monitoring

**For Tonight:**
- **Skip FastAPI** - Focus on Streamlit UI
- Use shared service layer (easy to add API later)
- Document API endpoints you would create

**For Future:**
- **Add FastAPI** - Reuse existing services
- Both UIs call same business logic
- Separate deployment or combined

---

## Testing Strategy (Include in Tonight's MVP)

**Test Structure:**
```
tests/
├── __init__.py
├── conftest.py          # Pytest fixtures
├── test_backends.py     # Backend tests
├── test_database.py     # Database tests
├── test_generator.py    # Generation logic tests
└── test_export.py       # Export functionality tests
```

**conftest.py (Shared Fixtures):**
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from synth_data.database.models import Base

@pytest.fixture(scope="function")
def db_session():
    """Provide a clean database session for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def sample_schema():
    """Provide a sample schema for testing."""
    return {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0, "maximum": 120}
    }

@pytest.fixture
def mock_api_key():
    """Provide a mock API key."""
    return "test_api_key_12345"
```

**test_backends.py:**
```python
import pytest
from synth_data.backends import HuggingFaceAPIBackend
from synth_data.backends.base import APIKeyError

class TestHuggingFaceBackend:
    """Test HuggingFace API backend."""

    def test_init_with_valid_key(self, mock_api_key):
        """Test initialization with valid API key."""
        backend = HuggingFaceAPIBackend(api_key=mock_api_key)
        assert backend.api_key == mock_api_key

    def test_init_without_key_stores_none(self):
        """Test initialization without API key."""
        backend = HuggingFaceAPIBackend()
        assert backend.api_key is None

    def test_generate_without_key_raises_error(self, sample_schema):
        """Test that generate without API key raises error."""
        backend = HuggingFaceAPIBackend()
        with pytest.raises(APIKeyError, match="API key required"):
            backend.generate(sample_schema, num_records=10)

    @pytest.mark.skip(reason="Requires real API key")
    def test_generate_with_real_api(self, sample_schema):
        """Integration test with real API (skip by default)."""
        import os
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            pytest.skip("HUGGINGFACE_API_KEY not set")

        backend = HuggingFaceAPIBackend(api_key=api_key)
        result = backend.generate(sample_schema, num_records=5)
        assert len(result) == 5
```

**test_database.py:**
```python
import pytest
from datetime import datetime
from synth_data.database.service import DatabaseService
from synth_data.database.models import Generation

class TestDatabaseService:
    """Test database operations."""

    def test_save_generation(self, db_session, sample_schema):
        """Test saving a generation to database."""
        service = DatabaseService(session=db_session)

        generation_id = service.save_generation(
            schema=sample_schema,
            num_records=10,
            data=[{"name": "Alice", "age": 30}]
        )

        assert generation_id is not None
        generation = db_session.query(Generation).filter_by(
            id=generation_id
        ).first()
        assert generation is not None
        assert generation.num_records == 10

    def test_get_recent_generations(self, db_session, sample_schema):
        """Test retrieving recent generations."""
        service = DatabaseService(session=db_session)

        # Save multiple generations
        for i in range(5):
            service.save_generation(
                schema=sample_schema,
                num_records=i+1,
                data=[]
            )

        # Retrieve recent
        recent = service.get_recent_generations(limit=3)
        assert len(recent) == 3
        # Should be in descending order by date
        assert recent[0].num_records == 5

    def test_delete_generation(self, db_session, sample_schema):
        """Test deleting a generation."""
        service = DatabaseService(session=db_session)

        generation_id = service.save_generation(
            schema=sample_schema,
            num_records=10,
            data=[]
        )

        # Delete
        service.delete_generation(generation_id)

        # Verify deleted
        generation = db_session.query(Generation).filter_by(
            id=generation_id
        ).first()
        assert generation is None
```

**test_generator.py:**
```python
import pytest
from synth_data.services.generator import GeneratorService

class TestGeneratorService:
    """Test data generation service."""

    def test_parse_schema(self, sample_schema):
        """Test schema parsing."""
        service = GeneratorService()
        parsed = service._parse_schema(sample_schema)
        assert "name" in parsed
        assert "age" in parsed

    def test_build_prompt(self, sample_schema):
        """Test prompt building from schema."""
        service = GeneratorService()
        prompt = service._build_prompt(sample_schema, num_records=10)
        assert "10" in prompt
        assert "name" in prompt
        assert "age" in prompt

    def test_validate_generated_data(self, sample_schema):
        """Test data validation against schema."""
        service = GeneratorService()

        # Valid data
        valid_data = [{"name": "Alice", "age": 30}]
        assert service._validate_data(valid_data, sample_schema)

        # Invalid data (age out of range)
        invalid_data = [{"name": "Bob", "age": 150}]
        assert not service._validate_data(invalid_data, sample_schema)
```

**Run Tests:**
```bash
# All tests
pytest

# With coverage
pytest --cov=synth_data --cov-report=html

# Specific test file
pytest tests/test_backends.py

# Specific test
pytest tests/test_backends.py::TestHuggingFaceBackend::test_init_with_valid_key

# Skip integration tests
pytest -m "not integration"
```

**Tonight's Test Coverage Goal:**
- Backends: 80%+
- Database: 90%+
- Generator: 70%+
- Overall: 75%+
