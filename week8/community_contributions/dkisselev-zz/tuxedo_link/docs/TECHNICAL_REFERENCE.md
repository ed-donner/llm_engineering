# 📚 Tuxedo Link - Complete Technical Reference

**Purpose**: Comprehensive documentation of all functions and components  

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Application Flow Overview](#application-flow-overview)
3. [Configuration System](#configuration-system)
4. [Email Provider System](#email-provider-system)
5. [Semantic Color/Breed Matching](#semantic-colorbreed-matching) **NEW v2.1**
6. [Alert Management](#alert-management)
7. [Frontend Layer (Gradio UI)](#frontend-layer-gradio-ui)
8. [Framework Layer](#framework-layer)
9. [Agent Layer](#agent-layer)
10. [Database Layer](#database-layer)
11. [Vector Database](#vector-database)
12. [Models Layer](#models-layer)
13. [Utilities Layer](#utilities-layer)
14. [Modal Services](#modal-services)
15. [Complete User Journey Examples](#complete-user-journey-examples)

---

## Project Structure

```
tuxedo_link/
├── agents/                     # Agentic components
│   ├── agent.py               # Base agent with colored logging
│   ├── petfinder_agent.py     # Petfinder API integration
│   ├── rescuegroups_agent.py  # RescueGroups API integration
│   ├── profile_agent.py       # GPT-4 profile extraction
│   ├── matching_agent.py      # Hybrid search & ranking
│   ├── deduplication_agent.py # 3-tier deduplication
│   ├── planning_agent.py      # Pipeline orchestration
│   ├── email_agent.py         # Email notifications
│   └── email_providers/       # Email provider system
│       ├── base.py            # Provider interface
│       ├── mailgun_provider.py # Mailgun implementation
│       ├── sendgrid_provider.py # SendGrid stub
│       └── factory.py         # Provider factory
├── models/                     # Pydantic data models
│   └── cats.py                # Cat, CatProfile, CatMatch, AdoptionAlert, SearchResult
├── database/                   # Persistence layer
│   ├── schema.py              # SQLite table definitions
│   └── manager.py             # Database CRUD operations
├── utils/                      # Utility functions
│   ├── config.py              # Configuration management
│   ├── color_mapping.py       # Color normalization (NEW v2.1)
│   ├── breed_mapping.py       # Breed normalization (NEW v2.1)
│   ├── deduplication.py       # Fingerprinting, Levenshtein, composite scoring
│   ├── image_utils.py         # CLIP image embeddings
│   ├── geocoding.py           # Location services
│   ├── log_utils.py           # Logging helpers
│   └── timing.py              # Performance decorators
├── tests/                      # Test suite (92 tests ✅)
│   ├── unit/                  # Unit tests (81 tests)
│   │   ├── test_models.py
│   │   ├── test_database.py
│   │   ├── test_deduplication.py
│   │   ├── test_email_providers.py
│   │   ├── test_metadata_vectordb.py (NEW v2.1)
│   │   ├── test_color_mapping.py (NEW v2.1)
│   │   └── test_breed_mapping.py (NEW v2.1)
│   ├── integration/           # Integration tests (11 tests)
│   │   ├── test_search_pipeline.py
│   │   ├── test_alerts.py
│   │   ├── test_app.py
│   │   └── test_color_breed_normalization.py (NEW v2.1)
│   ├── manual/                # Manual test scripts (4 scripts)
│   │   ├── test_cache_and_dedup.py
│   │   └── test_email_sending.py
│   ├── conftest.py            # Pytest fixtures
│   └── README.md              # Testing guide
├── scripts/                    # Deployment & utility scripts
│   ├── upload_config_to_modal.py # Config upload helper
│   ├── fetch_valid_colors.py     # API color/breed fetcher (NEW v2.1)
│   └── test_semantic_matching.py # Manual semantic test (NEW v2.1)
├── modal_services/             # Modal serverless deployment
│   └── scheduled_search.py    # Scheduled jobs (daily/weekly/immediate)
├── docs/                       # Documentation
│   ├── MODAL_DEPLOYMENT.md         # Deployment guide
│   ├── TECHNICAL_REFERENCE.md      # This file - complete technical docs
│   └── architecture_diagrams/      # Visual diagrams
├── data/                       # SQLite databases
│   └── tuxedo_link.db         # Main database (git-ignored)
├── cat_vectorstore/            # ChromaDB vector store (cat profiles)
│   └── chroma.sqlite3         # Persistent embeddings (git-ignored)
├── metadata_vectorstore/       # ChromaDB metadata store (colors/breeds) (NEW v2.1)
│   └── chroma.sqlite3         # Persistent metadata embeddings (git-ignored)
├── assets/                     # Static assets
│   └── Kyra.png               # Cat photo for About tab
├── app.py                      # Gradio web interface
├── cat_adoption_framework.py   # Main framework class
├── setup_vectordb.py           # Cat vector DB initialization
├── setup_metadata_vectordb.py  # Metadata vector DB initialization (NEW v2.1)
├── run.sh                      # Local launch script
├── deploy.sh                   # Modal deployment script (NEW)
├── pyproject.toml              # Python project config
├── requirements.txt            # Pip dependencies
├── config.example.yaml         # Configuration template (NEW)
├── env.example                 # Environment template
└── README.md                   # Quick start guide
```

### Key Components

**Agents** - Specialized components for specific tasks:
- `PlanningAgent` - Orchestrates the entire search pipeline
- `ProfileAgent` - Extracts structured preferences from natural language
- `PetfinderAgent` / `RescueGroupsAgent` - API integrations
- `DeduplicationAgent` - Three-tier duplicate detection
- `MatchingAgent` - Hybrid search with ranking
- `EmailAgent` - Notification system

**Data Models** - Pydantic schemas for type safety:
- `Cat` - Individual cat record
- `CatProfile` - User search preferences
- `CatMatch` - Ranked match with explanation
- `AdoptionAlert` - Email alert subscription
- `SearchResult` - Complete search response

**Database** - Dual persistence:
- SQLite - Cat cache, image embeddings, alerts
- ChromaDB - Vector embeddings for semantic search

**Tests** - Comprehensive test suite:
- Unit tests for individual components
- Integration tests for end-to-end flows
- Manual scripts for real API testing

---

## Application Flow Overview

### High-Level Flow

```
User Input (Gradio UI)
    ↓
extract_profile_from_text()  [app.py]
    ↓
ProfileAgent.extract_profile()  [profile_agent.py]
    ↓
TuxedoLinkFramework.search()  [cat_adoption_framework.py]
    ↓
PlanningAgent.search()  [planning_agent.py]
    ↓
├─→ PetfinderAgent.search_cats()  [petfinder_agent.py]
├─→ RescueGroupsAgent.search_cats()  [rescuegroups_agent.py]
    ↓
DeduplicationAgent.deduplicate()  [deduplication_agent.py]
    ↓
DatabaseManager.cache_cat()  [manager.py]
    ↓
VectorDBManager.add_cats()  [setup_vectordb.py]
    ↓
MatchingAgent.search()  [matching_agent.py]
    ↓
Results back to User (Gradio UI)
```

---

## Configuration System

**File**: `utils/config.py`  
**Purpose**: Centralized YAML-based configuration management with environment variable overrides

### Overview

The configuration system separates API keys (in `.env`) from application settings (in `config.yaml`), enabling:
- Deployment mode switching (local vs production)
- Email provider selection
- Database path configuration
- Easy configuration without code changes

### Core Functions

#### 1. `load_config()`

**Purpose**: Load and cache configuration from YAML file.

**Signature**:
```python
def load_config() -> Dict[str, Any]
```

**Returns**: Complete configuration dictionary

**Behavior**:
- First checks for `config.yaml`
- Falls back to `config.example.yaml` if not found
- Applies environment variable overrides
- Caches result for performance

**Example**:
```python
config = load_config()
# Returns:
# {
#   'email': {'provider': 'mailgun', ...},
#   'deployment': {'mode': 'local', ...},
#   ...
# }
```

#### 2. `is_production()`

**Purpose**: Check if running in production mode.

**Signature**:
```python
def is_production() -> bool
```

**Returns**: `True` if `deployment.mode == 'production'`, else `False`

**Usage**:
```python
if is_production():
    # Use Modal remote functions
    send_immediate_notification.remote(alert_id)
else:
    # Local mode - can't send immediate notifications
    print("Immediate notifications only available in production")
```

#### 3. `get_db_path()` / `get_vectordb_path()`

**Purpose**: Get database paths based on deployment mode.

**Signature**:
```python
def get_db_path() -> str
def get_vectordb_path() -> str
```

**Returns**:
- Local mode: `"data/tuxedo_link.db"`, `"cat_vectorstore"`
- Production mode: `"/data/tuxedo_link.db"`, `"/data/cat_vectorstore"`

**Example**:
```python
db_path = get_db_path()  # Automatically correct for current mode
db_manager = DatabaseManager(db_path)
```

#### 4. `get_email_provider()` / `get_email_config()` / `get_mailgun_config()`

**Purpose**: Get email-related configuration.

**Signatures**:
```python
def get_email_provider() -> str  # Returns "mailgun" or "sendgrid"
def get_email_config() -> Dict[str, str]  # Returns from_name, from_email
def get_mailgun_config() -> Dict[str, str]  # Returns domain
```

**Example**:
```python
provider_name = get_email_provider()  # "mailgun"
email_cfg = get_email_config()  
# {'from_name': 'Tuxedo Link', 'from_email': 'noreply@...'}
```

### Configuration File Structure

**`config.yaml`**:
```yaml
email:
  provider: mailgun
  from_name: "Tuxedo Link"
  from_email: "noreply@example.com"

mailgun:
  domain: "sandbox123.mailgun.org"

deployment:
  mode: local  # or production
  local:
    db_path: "data/tuxedo_link.db"
    vectordb_path: "cat_vectorstore"
  production:
    db_path: "/data/tuxedo_link.db"
    vectordb_path: "/data/cat_vectorstore"
```

### Environment Overrides

Environment variables can override config:
```bash
export EMAIL_PROVIDER=sendgrid  # Overrides config.yaml
export DEPLOYMENT_MODE=production
```

---

## Email Provider System

**Files**: `agents/email_providers/*.py`  
**Purpose**: Pluggable email backend system supporting multiple providers

### Architecture

```
EmailAgent
    ↓
get_email_provider()  [factory.py]
    ↓
├─→ MailgunProvider  [mailgun_provider.py]
└─→ SendGridProvider [sendgrid_provider.py] (stub)
    ↓
send_email() via requests or API
```

### Core Components

#### 1. `EmailProvider` (Base Class)

**File**: `agents/email_providers/base.py`

**Purpose**: Abstract interface all providers must implement.

**Methods**:
```python
class EmailProvider(ABC):
    @abstractmethod
    def send_email(
        self, 
        to: str, 
        subject: str, 
        html: str, 
        text: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass
```

#### 2. `MailgunProvider`

**File**: `agents/email_providers/mailgun_provider.py`

**Purpose**: Full Mailgun API implementation using requests library.

**Initialization**:
```python
provider = MailgunProvider()
# Reads:
# - MAILGUN_API_KEY from environment
# - mailgun.domain from config.yaml
# - email.from_name, email.from_email from config.yaml
```

**Key Methods**:

**`send_email()`**:
```python
def send_email(
    to: str, 
    subject: str, 
    html: str, 
    text: str,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None
) -> bool
```

**Example**:
```python
provider = MailgunProvider()
success = provider.send_email(
    to="user@example.com",
    subject="New Cat Matches!",
    html="<h1>Found 5 matches</h1>...",
    text="Found 5 matches..."
)
# Returns: True if sent, False if failed
```

**Implementation Details**:
- Uses `requests.post()` with `auth=("api", api_key)`
- Sends to `https://api.mailgun.net/v3/{domain}/messages`
- Returns `True` on status 200, `False` otherwise
- Logs all operations for debugging

#### 3. `SendGridProvider` (Stub)

**File**: `agents/email_providers/sendgrid_provider.py`

**Purpose**: Stub implementation for testing/backwards compatibility.

**Behavior**:
- Always returns `True` (simulates success)
- Logs what would be sent (doesn't actually send)
- Useful for testing without API calls

**Example**:
```python
provider = SendGridProvider()
success = provider.send_email(...)  # Always True
# Logs: "[STUB] Would send email via SendGrid to user@example.com"
```

#### 4. `get_email_provider()` (Factory)

**File**: `agents/email_providers/factory.py`

**Purpose**: Create provider instance based on configuration.

**Signature**:
```python
def get_email_provider(provider_name: Optional[str] = None) -> EmailProvider
```

**Parameters**:
- `provider_name`: Optional override (default: reads from config)

**Returns**: Configured provider instance

**Example**:
```python
# Use configured provider
provider = get_email_provider()  # Reads config.yaml

# Or specify explicitly
provider = get_email_provider('mailgun')
provider = get_email_provider('sendgrid')
```

### Integration with EmailAgent

**File**: `agents/email_agent.py`

**Modified** to use provider system:
```python
class EmailAgent(Agent):
    def __init__(self, provider: Optional[EmailProvider] = None):
        self.provider = provider or get_email_provider()
        self.enabled = True if self.provider else False
    
    def send_match_notification(self, alert, matches):
        # Build HTML/text templates
        html = self._build_match_html(matches, alert)
        text = self._build_match_text(matches)
        
        # Send via provider
        success = self.provider.send_email(
            to=alert.user_email,
            subject=f"🐱 {len(matches)} New Cat Matches!",
            html=html,
            text=text
        )
        return success
```

## Semantic Color/Breed Matching

**NEW in v2.1** - 3-tier intelligent normalization system for color and breed terms.

### Overview

The semantic matching system ensures user queries like "find me a tuxedo maine coon" are correctly translated to API values, even with typos ("tuxado", "main coon"). It uses a **3-tier strategy**:

1. **Dictionary Lookup** (< 1ms) - Common terms mapped instantly
2. **Vector DB Search** (10-50ms) - Fuzzy matching for typos
3. **String Matching** (< 1ms) - Fallback for edge cases

### Architecture

```
User Input → Profile Agent → Planning Agent → API Call
             ↓ (extract)    ↓ (normalize)
             "tuxedo"       1. Dictionary → "Black & White / Tuxedo"
                           2. Vector DB  → (if not found)
                           3. Fallback   → (if still not found)
```

### Components

#### 1. Metadata Vector Database (`setup_metadata_vectordb.py`)

Separate ChromaDB for color/breed fuzzy matching.

**Class**: `MetadataVectorDB`

**Initialization**:
```python
from setup_metadata_vectordb import MetadataVectorDB

vectordb = MetadataVectorDB("metadata_vectorstore")
```

**Key Methods**:

##### `index_colors(valid_colors: List[str], source: str)`

Indexes color values from an API.

```python
colors = ["Black", "White", "Black & White / Tuxedo"]
vectordb.index_colors(colors, source="petfinder")
```

##### `index_breeds(valid_breeds: List[str], source: str)`

Indexes breed values from an API.

```python
breeds = ["Siamese", "Maine Coon", "Ragdoll"]
vectordb.index_breeds(breeds, source="petfinder")
```

##### `search_color(user_term: str, n_results: int = 1, source_filter: Optional[str] = None)`

Find most similar color via semantic search.

**Returns**: `List[Dict]` with keys: `color`, `distance`, `similarity`, `source`

```python
results = vectordb.search_color("tuxado", n_results=1)
# [{"color": "Black & White / Tuxedo", "similarity": 0.85, "source": "petfinder"}]
```

##### `search_breed(user_term: str, n_results: int = 1, source_filter: Optional[str] = None)`

Find most similar breed via semantic search.

```python
results = vectordb.search_breed("ragdol", n_results=1)
# [{"breed": "Ragdoll", "similarity": 0.92, "source": "petfinder"}]
```

##### `get_stats()`

Get statistics about indexed data.

```python
stats = vectordb.get_stats()
# {"colors_count": 48, "breeds_count": 102}
```

---

#### 2. Color Mapping (`utils/color_mapping.py`)

Normalizes user color terms to valid API values.

**Dictionary**: `USER_TERM_TO_API_COLOR` - 40+ mappings

**Key examples**:
- `"tuxedo"` → `["Black & White / Tuxedo"]`
- `"orange tabby"` → `["Tabby (Orange / Red)"]`
- `"gray"` / `"grey"` → `["Gray / Blue / Silver"]`

##### `normalize_user_colors(user_colors, valid_api_colors, vectordb=None, source="petfinder", similarity_threshold=0.7)`

3-tier normalization for colors.

**Parameters**:
- `user_colors`: List of user color terms
- `valid_api_colors`: Valid colors from API
- `vectordb`: Optional MetadataVectorDB for fuzzy matching
- `source`: API source filter ("petfinder"/"rescuegroups")
- `similarity_threshold`: Minimum similarity (0-1) for vector matches

**Returns**: `List[str]` - Valid API color values

**Example**:
```python
from utils.color_mapping import normalize_user_colors

valid_colors = ["Black", "White", "Black & White / Tuxedo"]

# Tier 1: Dictionary
result = normalize_user_colors(["tuxedo"], valid_colors)
# ["Black & White / Tuxedo"]

# Tier 2: Vector DB (with typo)
result = normalize_user_colors(
    ["tuxado"],  # Typo!
    valid_colors,
    vectordb=metadata_vectordb,
    source="petfinder",
    similarity_threshold=0.6
)
# ["Black & White / Tuxedo"] (if similarity >= 0.6)

# Tier 3: Fallback
result = normalize_user_colors(["Black"], valid_colors)
# ["Black"] (exact match)
```

**Logging**:
```
🎯 Dictionary match: 'tuxedo' → ['Black & White / Tuxedo']
🔍 Vector match: 'tuxado' → 'Black & White / Tuxedo' (similarity: 0.85)
✓ Exact match: 'Black' → 'Black'
≈ Substring match: 'tabby' → 'Tabby (Brown / Chocolate)'
⚠️ No color match found for 'invalid_color'
```

##### `get_color_suggestions(color_term, valid_colors, top_n=5)`

Get color suggestions for autocomplete.

```python
suggestions = get_color_suggestions("tab", valid_colors, top_n=3)
# ["Tabby (Brown / Chocolate)", "Tabby (Orange / Red)", "Tabby (Gray / Blue / Silver)"]
```

---

#### 3. Breed Mapping (`utils/breed_mapping.py`)

Normalizes user breed terms to valid API values.

**Dictionary**: `USER_TERM_TO_API_BREED` - 30+ mappings

**Key examples**:
- `"main coon"` → `["Maine Coon"]`
- `"ragdol"` → `["Ragdoll"]`
- `"sphinx"` → `["Sphynx"]`
- `"dsh"` → `["Domestic Short Hair"]`
- `"mixed"` → `["Mixed Breed", "Domestic Short Hair", ...]`

##### `normalize_user_breeds(user_breeds, valid_api_breeds, vectordb=None, source="petfinder", similarity_threshold=0.7)`

3-tier normalization for breeds.

**Parameters**: Same as `normalize_user_colors`

**Returns**: `List[str]` - Valid API breed values

**Example**:
```python
from utils.breed_mapping import normalize_user_breeds

valid_breeds = ["Siamese", "Maine Coon", "Ragdoll"]

# Tier 1: Dictionary (typo correction)
result = normalize_user_breeds(["main coon"], valid_breeds)
# ["Maine Coon"]

# Tier 2: Vector DB
result = normalize_user_breeds(
    ["ragdol"],
    valid_breeds,
    vectordb=metadata_vectordb,
    source="petfinder"
)
# ["Ragdoll"]

# Special: Mixed breeds
result = normalize_user_breeds(["mixed"], valid_breeds)
# ["Mixed Breed", "Domestic Short Hair", "Domestic Medium Hair"]
```

##### `get_breed_suggestions(breed_term, valid_breeds, top_n=5)`

Get breed suggestions for autocomplete.

```python
suggestions = get_breed_suggestions("short", valid_breeds, top_n=3)
# ["Domestic Short Hair", "British Shorthair", "American Shorthair"]
```

---

#### 4. Agent Integration

##### PetfinderAgent

**New Methods**:

###### `get_valid_colors() -> List[str]`

Fetch all valid cat colors from Petfinder API (`/v2/types/cat`).

**Returns**: 30 colors (cached)

```python
agent = PetfinderAgent()
colors = agent.get_valid_colors()
# ["Black", "Black & White / Tuxedo", "Blue Cream", ...]
```

###### `get_valid_breeds() -> List[str]`

Fetch all valid cat breeds from Petfinder API (`/v2/types/cat/breeds`).

**Returns**: 68 breeds (cached)

```python
breeds = agent.get_valid_breeds()
# ["Abyssinian", "American Curl", "American Shorthair", ...]
```

###### `search_cats(..., color: Optional[List[str]], breed: Optional[List[str]], ...)`

Search with **normalized** color and breed values.

```python
# User says "tuxedo maine coon"
# Planning agent normalizes:
# - "tuxedo" → ["Black & White / Tuxedo"]
# - "maine coon" → ["Maine Coon"]

results = agent.search_cats(
    location="NYC",
    color=["Black & White / Tuxedo"],  # Normalized!
    breed=["Maine Coon"],              # Normalized!
    limit=100
)
```

---

##### RescueGroupsAgent

**New Methods**:

###### `get_valid_colors() -> List[str]`

Fetch all valid cat colors from RescueGroups API (`/v5/public/animals/colors`).

**Returns**: 597 colors (cached)

```python
agent = RescueGroupsAgent()
colors = agent.get_valid_colors()
# ["Black", "White", "Gray", "Orange", "Tuxedo", ...]
```

###### `get_valid_breeds() -> List[str]`

Fetch all valid cat breeds from RescueGroups API (`/v5/public/animals/breeds`).

**Returns**: 807 breeds (cached)

```python
breeds = agent.get_valid_breeds()
# ["Domestic Short Hair", "Siamese", "Maine Coon", ...]
```

###### `search_cats(..., color: Optional[List[str]], breed: Optional[List[str]], ...)`

**Note**: RescueGroups API doesn't support direct color/breed filtering. Values are logged but filtered client-side.

```python
results = agent.search_cats(
    location="NYC",
    color=["Tuxedo"],   # Logged, filtered client-side
    breed=["Maine Coon"] # Logged, filtered client-side
)
```

---

##### PlanningAgent

**Modified Methods**:

###### `_search_petfinder(profile: CatProfile)`

Now normalizes colors and breeds before API call.

```python
# User profile
profile = CatProfile(
    color_preferences=["tuxedo", "orange tabby"],
    preferred_breeds=["main coon", "ragdol"]  # Typos!
)

# Planning agent normalizes:
# 1. Fetches valid colors/breeds from API
# 2. Runs 3-tier normalization
# 3. Passes normalized values to API

# Logs:
# ✓ Colors: ['tuxedo', 'orange tabby'] → ['Black & White / Tuxedo', 'Tabby (Orange / Red)']
# ✓ Breeds: ['main coon', 'ragdol'] → ['Maine Coon', 'Ragdoll']
```

---

#### 5. Framework Integration

##### TuxedoLinkFramework

**New Initialization Step**: `_index_metadata()`

Called during framework initialization to populate metadata vector DB.

```python
def _index_metadata(self):
    """Index colors and breeds from APIs."""
    
    # Fetch and index Petfinder
    petfinder = PetfinderAgent()
    colors = petfinder.get_valid_colors()  # 30 colors
    breeds = petfinder.get_valid_breeds()  # 68 breeds
    self.metadata_vectordb.index_colors(colors, source="petfinder")
    self.metadata_vectordb.index_breeds(breeds, source="petfinder")
    
    # Fetch and index RescueGroups
    rescuegroups = RescueGroupsAgent()
    colors = rescuegroups.get_valid_colors()  # 597 colors
    breeds = rescuegroups.get_valid_breeds()  # 807 breeds
    self.metadata_vectordb.index_colors(colors, source="rescuegroups")
    self.metadata_vectordb.index_breeds(breeds, source="rescuegroups")
    
    # Log stats
    stats = self.metadata_vectordb.get_stats()
    # ✓ Metadata indexed: 48 colors, 102 breeds
```

**Performance**: ~2-5 seconds on first run, then cached.

---

### Complete Flow Example

```python
from cat_adoption_framework import TuxedoLinkFramework
from models.cats import CatProfile

# 1. Initialize framework (auto-indexes metadata)
framework = TuxedoLinkFramework()
# [INFO] ✓ Fetched 30 valid colors from Petfinder
# [INFO] ✓ Fetched 68 valid breeds from Petfinder
# [INFO] ✓ Fetched 597 valid colors from RescueGroups
# [INFO] ✓ Fetched 807 valid breeds from RescueGroups
# [INFO] ✓ Metadata indexed: 48 colors, 102 breeds

# 2. User searches with natural language (with typos!)
profile = CatProfile(
    user_location="Boston, MA",
    color_preferences=["tuxado", "ornage tabby"],  # Typos!
    preferred_breeds=["main coon", "ragdol"],      # Typos!
    max_distance=50
)

# 3. Framework normalizes and searches
result = framework.search(profile)

# Behind the scenes:
# [INFO] 🎯 Dictionary match: 'main coon' → ['Maine Coon']
# [INFO] 🎯 Dictionary match: 'ragdol' → ['Ragdoll']
# [INFO] 🔍 Vector match: 'tuxado' → 'Black & White / Tuxedo' (similarity: 0.85)
# [INFO] 🔍 Vector match: 'ornage tabby' → 'Tabby (Orange / Red)' (similarity: 0.78)
# [INFO] ✓ Colors: ['tuxado', 'ornage tabby'] → ['Black & White / Tuxedo', 'Tabby (Orange / Red)']
# [INFO] ✓ Breeds: ['main coon', 'ragdol'] → ['Maine Coon', 'Ragdoll']

# 4. APIs receive normalized values
# Petfinder.search_cats(color=['Black & White / Tuxedo', 'Tabby (Orange / Red)'], breed=['Maine Coon', 'Ragdoll'])
# RescueGroups.search_cats(color=['Black & White / Tuxedo', 'Tabby (Orange / Red)'], breed=['Maine Coon', 'Ragdoll'])

# 5. Results returned
print(f"Found {len(result.matches)} matches!")
```

---

### Configuration

No configuration needed! The system:
- ✅ Automatically fetches valid colors/breeds from APIs
- ✅ Indexes them on startup (persisted to disk)
- ✅ Uses 3-tier strategy transparently
- ✅ Logs all normalization steps for debugging

**Optional**: Adjust similarity threshold in planning agent:

```python
# In agents/planning_agent.py
api_colors = normalize_user_colors(
    profile.color_preferences,
    valid_colors,
    vectordb=self.metadata_vectordb,
    source="petfinder",
    similarity_threshold=0.8  # Default: 0.7
)
```

---

### Summary

The semantic color/breed matching system provides:

✅ **Natural Language**: Users can use terms like "tuxedo", "orange tabby"  
✅ **Typo Tolerance**: "tuxado" → "tuxedo", "main coon" → "Maine Coon"  
✅ **3-Tier Strategy**: Dictionary → Vector → Fallback (99%+ coverage)  
✅ **Fast**: < 50ms overhead per search  
✅ **Automatic**: No configuration required  
✅ **Multi-API**: Works with Petfinder & RescueGroups  
✅ **Well-Tested**: 46 unit tests + 8 integration tests  
✅ **Extensible**: Easy to add new mappings or APIs  

**Impact**: Users can now search naturally without needing to know exact API color/breed values, resulting in better search results and improved adoption rates! 🐱

---

## Alert Management

**File**: `app.py`  
**Purpose**: UI functions for managing email alerts without authentication

### Overview

The alert system allows users to save searches and receive email notifications. Key features:
- No authentication required - alerts tied to email address
- Three frequencies: Immediately, Daily, Weekly
- Full CRUD operations via Gradio UI
- Email validation
- Real-time alert display

### Core Functions

#### 1. `save_alert()`

**Purpose**: Save current search profile as an email alert.

**Signature**:
```python
def save_alert(
    email: str, 
    frequency: str, 
    profile_json: str
) -> Tuple[str, pd.DataFrame]
```

**Parameters**:
- `email`: User's email address
- `frequency`: "Immediately", "Daily", or "Weekly"
- `profile_json`: JSON of current search profile

**Returns**:
- Tuple of (status_message, updated_alerts_dataframe)

**Behavior**:
1. Validates email format
2. Checks that a search profile exists
3. Creates `AdoptionAlert` with email and profile
4. Saves to database
5. If frequency == "immediately" and production mode: triggers Modal notification
6. Returns success message and refreshed alert list

**Example**:
```python
# User saves search as alert
status, alerts_df = save_alert(
    email="user@example.com",
    frequency="daily",
    profile_json="{...current profile...}"
)
# Returns:
# ("✅ Alert saved successfully! (ID: 5)\n\nYou'll receive daily notifications at user@example.com",
#  DataFrame with all alerts)
```

#### 2. `load_alerts()`

**Purpose**: Load all alerts from database, optionally filtered by email.

**Signature**:
```python
def load_alerts(email_filter: str = "") -> pd.DataFrame
```

**Parameters**:
- `email_filter`: Optional email to filter by

**Returns**: DataFrame with columns:
- ID, Email, Frequency, Location, Preferences, Last Sent, Status

**Example**:
```python
# Load all alerts
all_alerts = load_alerts()

# Load alerts for specific email
my_alerts = load_alerts("user@example.com")
```

#### 3. `delete_alert()`

**Purpose**: Delete an alert by ID.

**Signature**:
```python
def delete_alert(
    alert_id: str, 
    email_filter: str = ""
) -> Tuple[str, pd.DataFrame]
```

**Parameters**:
- `alert_id`: ID of alert to delete
- `email_filter`: Optional email filter for refresh

**Returns**: Tuple of (status_message, updated_alerts_dataframe)

**Example**:
```python
status, alerts_df = delete_alert("5", "")
# Returns: ("✅ Alert 5 deleted successfully", updated DataFrame)
```

#### 4. `toggle_alert_status()`

**Purpose**: Toggle alert between active and inactive.

**Signature**:
```python
def toggle_alert_status(
    alert_id: str, 
    email_filter: str = ""
) -> Tuple[str, pd.DataFrame]
```

**Returns**: Tuple of (status_message, updated_alerts_dataframe)

**Example**:
```python
# Deactivate alert
status, alerts_df = toggle_alert_status("5", "")
# Returns: ("✅ Alert 5 deactivated", updated DataFrame)

# Activate again
status, alerts_df = toggle_alert_status("5", "")
# Returns: ("✅ Alert 5 activated", updated DataFrame)
```

#### 5. `validate_email()`

**Purpose**: Validate email address format.

**Signature**:
```python
def validate_email(email: str) -> bool
```

**Returns**: `True` if valid email format, `False` otherwise

**Example**:
```python
validate_email("user@example.com")  # True
validate_email("invalid-email")  # False
```

### UI Components

**Alerts Tab Structure**:
1. **Save Alert Section**
   - Email input field
   - Frequency dropdown (Immediately/Daily/Weekly)
   - Save button
   - Status message

2. **Manage Alerts Section**
   - Email filter input
   - Refresh button
   - DataTable displaying all alerts
   - Alert ID input
   - Toggle active/inactive button
   - Delete button
   - Action status message

**Event Wiring**:
```python
# Save button
save_btn.click(
    fn=save_alert,
    inputs=[email_input, frequency_dropdown, profile_display],
    outputs=[save_status, alerts_table]
)

# Delete button
delete_btn.click(
    fn=delete_alert,
    inputs=[alert_id_input, email_filter_input],
    outputs=[action_status, alerts_table]
)
```

---

## Frontend Layer (Gradio UI)

**File**: `app.py`  
**Purpose**: User interface and interaction handling

### Core Functions

#### 1. `extract_profile_from_text()`

**Purpose**: Main entry point for user searches. Converts natural language to structured search.

**Signature**:
```python
def extract_profile_from_text(
    user_text: str, 
    use_cache: bool = True
) -> tuple[List[dict], str, str]
```

**Parameters**:
- `user_text`: Natural language description (e.g., "friendly cat in NYC")
- `use_cache`: Whether to use cached data (default: True for dev)

**Returns**:
- Tuple of (chat_history, results_html, profile_display)
  - `chat_history`: List of message dicts in OpenAI prompt format
  - `results_html`: HTML grid of cat cards
  - `profile_display`: JSON string of extracted profile

**Integration**:
```
Called by: Gradio UI (user input)
Calls:
  → ProfileAgent.extract_profile()
  → TuxedoLinkFramework.search()
  → build_results_grid()
```

**Example**:
```python
# User types: "I want a playful kitten in NYC, good with kids"
chat_history, results_html, profile = extract_profile_from_text(
    "I want a playful kitten in NYC, good with kids",
    use_cache=True
)

# Returns:
# - chat_history: [
#     {"role": "user", "content": "I want a playful kitten..."},
#     {"role": "assistant", "content": "✅ Got it! Found 15 cats..."}
#   ]
# - results_html: "<div>...</div>" (HTML grid of cats)
# - profile: '{"user_location": "NYC", "age_range": ["kitten"], ...}'
```

**Flow**:
1. Check for empty input → use placeholder if blank
2. Convert text to conversation format (list of message dicts)
3. Extract structured profile using ProfileAgent
4. Execute search via Framework
5. Format results as HTML grid
6. Return messages in OpenAI format for Gradio

---

#### 2. `build_results_grid()`

**Purpose**: Convert cat matches into HTML grid for display.

**Signature**:
```python
def build_results_grid(matches: List[CatMatch]) -> str
```

**Parameters**:
- `matches`: List of CatMatch objects with cat data and scores

**Returns**:
- HTML string with grid layout

**Integration**:
```
Called by: extract_profile_from_text()
Uses: CatMatch.cat, CatMatch.match_score, CatMatch.explanation
```

**Example**:
```python
matches = [
    CatMatch(
        cat=Cat(name="Fluffy", breed="Persian", ...),
        match_score=0.85,
        explanation="Great personality match"
    ),
    # ... more matches
]

html = build_results_grid(matches)
# Returns:
# <div style='display: grid; ...'>
#   <div class='cat-card'>
#     <img src='...' />
#     <h3>Fluffy (85% match)</h3>
#     <p>Great personality match</p>
#   </div>
#   ...
# </div>
```

---

#### 3. `build_search_tab()`

**Purpose**: Construct the search interface with chat and results display.

**Signature**:
```python
def build_search_tab() -> None
```

**Integration**:
```
Called by: create_app()
Creates:
  → Chatbot component
  → Text input
  → Search button
  → Results display
  → Example buttons
```

**Components Created**:
- `chatbot`: Conversation history display
- `user_input`: Text box for cat description
- `search_btn`: Trigger search
- `results_html`: Display cat cards
- `use_cache_checkbox`: Toggle cache mode

---

#### 4. `create_app()`

**Purpose**: Initialize and configure the complete Gradio application.

**Signature**:
```python
def create_app() -> gr.Blocks
```

**Returns**:
- Configured Gradio Blocks application

**Integration**:
```
Called by: __main__
Creates:
  → Search tab (build_search_tab)
  → Alerts tab (build_alerts_tab)
  → About tab (build_about_tab)
```

**Example**:
```python
app = create_app()
app.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=False
)
```

---

## Framework Layer

**File**: `cat_adoption_framework.py`  
**Purpose**: Main orchestrator that coordinates all components

### Core Class: `TuxedoLinkFramework`

#### 1. `__init__()`

**Purpose**: Initialize framework with database and vector store.

**Signature**:
```python
def __init__(self) -> None
```

**Integration**:
```
Creates:
  → DatabaseManager (SQLite)
  → VectorDBManager (ChromaDB)
  → UserManager
Initializes:
  → Logging
  → Environment variables
```

**Example**:
```python
framework = TuxedoLinkFramework()
```

---

#### 2. `search()`

**Purpose**: Execute complete cat adoption search pipeline.

**Signature**:
```python
def search(
    self, 
    profile: CatProfile, 
    use_cache: bool = False
) -> SearchResult
```

**Parameters**:
- `profile`: Structured search criteria
- `use_cache`: Use cached data instead of API calls

**Returns**:
- `SearchResult` with ranked matches and metadata

**Integration**:
```
Called by: extract_profile_from_text() (app.py)
Calls:
  → init_agents() (lazy initialization)
  → PlanningAgent.search()
Returns to: Frontend for display
```

**Example**:
```python
profile = CatProfile(
    user_location="10001",
    age_range=["young"],
    personality_description="friendly playful"
)

result = framework.search(profile, use_cache=False)
# Returns:
# SearchResult(
#   matches=[CatMatch(...), ...],  # Top 20 ranked
#   total_found=87,
#   search_time=13.5,
#   sources_queried=["petfinder", "rescuegroups"],
#   duplicates_removed=12
# )
```

**Pipeline Steps**:
1. Initialize agents (if first call)
2. Delegate to PlanningAgent
3. Return structured results

---

#### 3. `init_agents()`

**Purpose**: Lazy initialization of agent pipeline.

**Signature**:
```python
def init_agents(self) -> None
```

**Integration**:
```
Called by: search()
Creates: PlanningAgent
```

**Example**:
```python
# First search - agents created
framework.search(profile)  # init_agents() called

# Second search - agents reused
framework.search(profile2)  # init_agents() skipped
```

---

#### 4. `get_stats()`

**Purpose**: Retrieve system statistics (database and vector store).

**Signature**:
```python
def get_stats(self) -> Dict[str, Any]
```

**Returns**:
```python
{
    'database': {
        'total_unique': 150,
        'total_duplicates': 25,
        'sources': 2,
        'by_source': {'petfinder': 100, 'rescuegroups': 50}
    },
    'vector_db': {
        'total_documents': 150,
        'collection_name': 'cats_embeddings'
    }
}
```

**Integration**:
```
Called by: Integration tests, monitoring
Uses:
  → DatabaseManager.get_cache_stats()
  → VectorDBManager.get_stats()
```

---

## Agent Layer

### Base Agent

**File**: `agents/agent.py`  
**Purpose**: Base class for all agents

#### Core Methods

##### 1. `log()`

**Purpose**: Log informational messages with agent identification.

**Signature**:
```python
def log(self, message: str) -> None
```

**Example**:
```python
class MyAgent(Agent):
    name = "My Agent"
    color = '\033[32m'  # Green

agent = MyAgent()
agent.log("Processing started")
# Output: [My Agent] Processing started
```

---

##### 2. `log_error()` / `log_warning()`

**Purpose**: Log errors and warnings with appropriate colors.

**Example**:
```python
agent.log_error("API call failed")
# Output: [My Agent] ERROR: API call failed

agent.log_warning("Rate limit approaching")
# Output: [My Agent] WARNING: Rate limit approaching
```

---

##### 3. `@timed` Decorator

**Purpose**: Automatically log execution time of methods.

**Signature**:
```python
def timed(func: Callable[..., Any]) -> Callable[..., Any]
```

**Example**:
```python
from agents.agent import timed

class SearchAgent(Agent):
    @timed
    def search(self):
        # ... search logic
        pass

agent.search()
# Output: [Agent] search completed in 2.34 seconds
```

---

### Planning Agent

**File**: `agents/planning_agent.py`  
**Purpose**: Orchestrate the entire search pipeline

#### Core Methods

##### 1. `search()`

**Purpose**: Coordinate all agents to complete a cat search.

**Signature**:
```python
def search(
    self, 
    profile: CatProfile, 
    use_cache: bool = False
) -> SearchResult
```

**Integration**:
```
Called by: TuxedoLinkFramework.search()
Orchestrates:
  1. fetch_cats() - Get from APIs
  2. deduplicate_and_cache() - Remove duplicates
  3. update_vector_db() - Store embeddings
  4. perform_matching() - Find best matches
```

**Example Flow**:
```python
planner = PlanningAgent(db_manager, vector_db)

result = planner.search(
    CatProfile(user_location="10001", age_range=["young"]),
    use_cache=False
)

# Executes:
# Step 1: Fetch from Petfinder & RescueGroups (parallel)
#   → 50 cats from Petfinder
#   → 50 cats from RescueGroups
# Step 2: Deduplicate (fingerprint + text + image)
#   → 88 unique cats (12 duplicates removed)
# Step 3: Cache & embed
#   → Store in SQLite
#   → Generate embeddings → ChromaDB
# Step 4: Match & rank
#   → Vector search: top 100 candidates
#   → Metadata filter: 42 match criteria
#   → Hybrid score: rank by 60% semantic + 40% attributes
#   → Return top 20
```

---

##### 2. `fetch_cats()`

**Purpose**: Retrieve cats from all API sources in parallel.

**Signature**:
```python
def fetch_cats(self, profile: CatProfile) -> Tuple[List[Cat], List[str]]
```

**Returns**:
- Tuple of (cats_list, sources_queried)

**Integration**:
```
Calls (parallel):
  → PetfinderAgent.search_cats()
  → RescueGroupsAgent.search_cats()
```

**Example**:
```python
cats, sources = planner.fetch_cats(profile)
# Returns:
# cats = [Cat(...), Cat(...), ...]  # 100 total
# sources = ["petfinder", "rescuegroups"]

# If one API fails:
# cats = [Cat(...), ...]  # 50 from working API
# sources = ["petfinder"]  # Only successful one
```

---

##### 3. `deduplicate_and_cache()`

**Purpose**: Remove duplicates and cache unique cats.

**Signature**:
```python
def deduplicate_and_cache(self, cats: List[Cat]) -> List[Cat]
```

**Integration**:
```
Calls:
  → DeduplicationAgent.deduplicate()
  → DatabaseManager.cache_cat() (for each unique)
```

**Example**:
```python
raw_cats = [cat1, cat2_dup, cat3, cat2_dup2]  # 4 cats
unique_cats = planner.deduplicate_and_cache(raw_cats)
# Returns: [cat1, cat3, cat2]  # 3 unique (1 duplicate removed)

# Side effect: All 3 cached in database with embeddings
```

---

##### 4. `update_vector_db()`

**Purpose**: Add cat embeddings to ChromaDB for semantic search.

**Signature**:
```python
def update_vector_db(self, cats: List[Cat]) -> None
```

**Integration**:
```
Calls: VectorDBManager.add_cats()
```

**Example**:
```python
cats = [cat1, cat2, cat3]
planner.update_vector_db(cats)

# Side effect:
# - Generates embeddings from description
# - Stores in ChromaDB collection
# - Available for vector search
```

---

##### 5. `perform_matching()`

**Purpose**: Find and rank best matches using hybrid search.

**Signature**:
```python
def perform_matching(self, profile: CatProfile) -> List[CatMatch]
```

**Integration**:
```
Calls: MatchingAgent.search()
```

**Example**:
```python
matches = planner.perform_matching(profile)
# Returns top 20 matches:
# [
#   CatMatch(cat=cat1, match_score=0.89, explanation="..."),
#   CatMatch(cat=cat2, match_score=0.85, explanation="..."),
#   ...
# ]
```

---

### Profile Agent

**File**: `agents/profile_agent.py`  
**Purpose**: Extract structured preferences from natural language

#### Core Method

##### `extract_profile()`

**Purpose**: Convert conversation messages to CatProfile using GPT-4.

**Signature**:
```python
def extract_profile(self, conversation: List[dict]) -> CatProfile
```

**Parameters**:
- `conversation`: List of message dicts with 'role' and 'content'
  - Format: `[{"role": "user", "content": "I want a friendly kitten..."}]`

**Returns**:
- Structured `CatProfile` object

**Integration**:
```
Called by: extract_profile_from_text() (app.py)
Uses: OpenAI GPT-4 with structured outputs
Format: OpenAI-compatible messages (role + content)
```

**Example**:
```python
agent = ProfileAgent()

# Conversation format
conversation = [{
    "role": "user",
    "content": "I want a friendly kitten in Brooklyn, NY that's good with kids and dogs"
}]

profile = agent.extract_profile(conversation)

# Returns:
# CatProfile(
#     user_location="Brooklyn, NY",
#     age_range=["kitten", "young"],
#     personality_description="friendly and social",
#     good_with_children=True,
#     good_with_dogs=True,
#     max_distance=50
# )
```

**How It Works**:
1. Receive conversation as list of message dicts
2. Add system prompt to messages
3. Send to OpenAI with CatProfile schema
4. GPT-4 parses intent and extracts preferences
5. Returns JSON matching CatProfile
6. Validate with Pydantic
7. Return structured object

```python
agent.extract_profile([{"role": "user", "content": "friendly cat"}])
```

---

### Petfinder Agent

**File**: `agents/petfinder_agent.py`  
**Purpose**: Integrate with Petfinder API (OAuth 2.0)

#### Core Methods

##### 1. `search_cats()`

**Purpose**: Search Petfinder API for cats matching criteria.

**Signature**:
```python
def search_cats(
    self,
    location: Optional[str] = None,
    distance: int = 100,
    age: Optional[str] = None,
    size: Optional[str] = None,
    gender: Optional[str] = None,
    good_with_children: Optional[bool] = None,
    good_with_dogs: Optional[bool] = None,
    good_with_cats: Optional[bool] = None,
    limit: int = 100
) -> List[Cat]
```

**Integration**:
```
Called by: PlanningAgent.fetch_cats()
Uses:
  → _get_access_token() (OAuth)
  → _rate_limit() (API limits)
  → _transform_petfinder_cat() (normalize data)
```

**Example**:
```python
agent = PetfinderAgent()

cats = agent.search_cats(
    location="10001",
    distance=50,
    age="young",
    good_with_children=True,
    limit=50
)

# Returns:
# [
#   Cat(
#     id="petfinder_12345",
#     name="Fluffy",
#     breed="Persian",
#     age="young",
#     source="petfinder",
#     url="https://petfinder.com/...",
#     ...
#   ),
#   ...
# ]  # Up to 50 cats
```

---

##### 2. `_get_access_token()`

**Purpose**: Obtain or refresh OAuth 2.0 access token.

**Integration**:
```
Called by: search_cats()
Manages: Token caching and expiration
```

**Example Flow**:
```python
# First call - get new token
# Second call (within 1 hour) - reuse token
# After expiration - refresh
token = agent._get_access_token()
# POST to /oauth2/token
# Store token + expiration time
# Return cached token
```

---

##### 3. `_rate_limit()`

**Purpose**: Enforce rate limiting (1 request/second).

**Example**:
```python
agent._rate_limit()  # Check time since last request
# If < 1 second: sleep(remaining_time)
# Update last_request_time
```

---

### RescueGroups Agent

**File**: `agents/rescuegroups_agent.py`  
**Purpose**: Integrate with RescueGroups.org API

#### Core Method

##### `search_cats()`

**Purpose**: Search RescueGroups API for cats.

**Signature**:
```python
def search_cats(
    self,
    location: Optional[str] = None,
    distance: int = 100,
    age: Optional[str] = None,
    size: Optional[str] = None,
    limit: int = 100
) -> List[Cat]
```

**Integration**:
```
Called by: PlanningAgent.fetch_cats()
```

**Example**:
```python
agent = RescueGroupsAgent()

cats = agent.search_cats(
    location="Brooklyn, NY",
    distance=25,
    age="kitten",
    limit=50
)
# Returns list of Cat objects from RescueGroups
```

---

### Deduplication Agent

**File**: `agents/deduplication_agent.py`  
**Purpose**: Remove duplicate cats across sources using 3-tier matching

#### Core Method

##### `deduplicate()`

**Purpose**: Find and mark duplicates using fingerprint + text + image similarity.

**Signature**:
```python
def deduplicate(self, cats: List[Cat]) -> List[Cat]
```

**Returns**:
- List of unique cats (duplicates marked in database)

**Integration**:
```
Called by: PlanningAgent.deduplicate_and_cache()
Uses:
  → create_fingerprint() (utils/deduplication.py)
  → calculate_levenshtein_similarity() (utils)
  → get_image_embedding() (utils/image_utils.py)
  → DatabaseManager.get_cats_by_fingerprint()
  → DatabaseManager.mark_as_duplicate()
```

**Example**:
```python
cats = [
    Cat(id="pf_1", name="Fluffy", breed="Persian", org="Happy Paws"),
    Cat(id="rg_2", name="Fluffy Jr", breed="Persian", org="Happy Paws"),
    Cat(id="pf_3", name="Max", breed="Tabby", org="Cat Rescue")
]

agent = DeduplicationAgent(db_manager)
unique = agent.deduplicate(cats)

# Process:
# 1. Create fingerprints
#    cat1: "happypaws_persian_adult_female"
#    cat2: "happypaws_persian_adult_female"  # SAME!
#    cat3: "catrescue_tabby_adult_male"
#
# 2. Check text similarity (name + description)
#    cat1 vs cat2: 85% similar (high!)
#
# 3. Check image similarity (if photos exist)
#    cat1 vs cat2: 92% similar (very high!)
#
# 4. Composite score with weights: (0.85 * 0.4) + (0.85 * 0.3) + (0.92 * 0.3) = 87%
#
# Result: cat2 marked as duplicate of cat1
# Returns: [cat1, cat3]
```

**Three-Tier Matching**:

1. **Fingerprint** (Organization + Breed + Age + Gender)
   ```python
   fingerprint = "happypaws_persian_adult_female"
   # Same fingerprint = likely duplicate
   ```

2. **Text Similarity** (Levenshtein distance on name + description)
   ```python
   similarity = calculate_levenshtein_similarity(
       "Fluffy the friendly cat",
       "Fluffy Jr - a friendly feline"
   )
   # Returns: 0.78 (78% similar)
   ```

3. **Image Similarity** (CLIP embeddings cosine similarity)
   ```python
   embed1 = get_image_embedding(cat1.primary_photo)
   embed2 = get_image_embedding(cat2.primary_photo)
   similarity = cosine_similarity(embed1, embed2)
   # Returns: 0.95 (95% similar - probably same cat!)
   ```

**Composite Score**:
```python
score = (
    name_similarity * 0.4 +
    description_similarity * 0.3 +
    image_similarity * 0.3
)
# If score > 0.75: Mark as duplicate
```

---

### Matching Agent

**File**: `agents/matching_agent.py`  
**Purpose**: Hybrid search combining vector similarity and metadata filtering

#### Core Methods

##### 1. `search()`

**Purpose**: Find best matches using semantic search + hard filters.

**Signature**:
```python
def search(
    self, 
    profile: CatProfile, 
    top_k: int = 20
) -> List[CatMatch]
```

**Returns**:
- Ranked list of CatMatch objects with scores and explanations

**Integration**:
```
Called by: PlanningAgent.perform_matching()
Uses:
  → VectorDBManager.search() (semantic search)
  → _apply_metadata_filters() (hard constraints)
  → _calculate_attribute_score() (metadata match)
  → _generate_explanation() (human-readable why)
```

**Example**:
```python
agent = MatchingAgent(db_manager, vector_db)

matches = agent.search(
    CatProfile(
        personality_description="friendly lap cat",
        age_range=["young", "adult"],
        good_with_children=True,
        max_distance=50
    ),
    top_k=10
)

# Process:
# Step 1: Vector search
#   Query: "friendly lap cat"
#   ChromaDB returns top 100 semantically similar
#
# Step 2: Metadata filtering
#   Filter by: age in [young, adult]
#             good_with_children == True
#             distance <= 50 miles
#   Result: 42 cats pass filters
#
# Step 3: Hybrid scoring
#   For each cat:
#     vector_score = 0.87 (from ChromaDB)
#     attribute_score = 0.75 (3 of 4 attrs match)
#     final_score = 0.87 * 0.6 + 0.75 * 0.4 = 0.822
#
# Step 4: Rank and explain
#   Sort by final_score descending
#   Generate explanations
#   Return top 10

# Returns:
# [
#   CatMatch(
#     cat=Cat(name="Fluffy", ...),
#     match_score=0.822,
#     vector_similarity=0.87,
#     attribute_match_score=0.75,
#     explanation="Fluffy is a great match! Described as friendly and loves laps. Good with children.",
#     matching_attributes=["personality", "age", "good_with_children"],
#     missing_attributes=["indoor_only"]
#   ),
#   ...
# ]
```

---

##### 2. `_apply_metadata_filters()`

**Purpose**: Apply hard constraints from user preferences.

**Example**:
```python
candidates = [cat1, cat2, cat3, ...]  # 100 cats

filtered = agent._apply_metadata_filters(candidates, profile)

# Applies:
# - age_range: ["young", "adult"]
# - good_with_children: True
# - max_distance: 50 miles
#
# cat1: age=young, good_with_children=True, distance=10 → PASS
# cat2: age=senior, good_with_children=True, distance=10 → FAIL (age)
# cat3: age=young, good_with_children=False, distance=10 → FAIL (children)

# Returns: [cat1, ...]
```

---

##### 3. `_generate_explanation()`

**Purpose**: Create human-readable match explanation.

**Example**:
```python
explanation = agent._generate_explanation(
    cat=Cat(name="Fluffy", description="Loves to cuddle"),
    profile=CatProfile(personality_description="lap cat"),
    attribute_score=0.75
)

# Returns:
# "Fluffy is a great match! Described as loving to cuddle, which aligns with your preference for a lap cat. Good with children and located nearby."
```

---

### Email Agent

**File**: `agents/email_agent.py`  
**Purpose**: Send email notifications via SendGrid

#### Core Method

##### `send_match_notification()`

**Purpose**: Email user about new cat matches.

**Signature**:
```python
def send_match_notification(
    self, 
    alert: AdoptionAlert, 
    matches: List[CatMatch]
) -> bool
```

**Integration**:
```
Called by: Modal scheduled_search.py (scheduled jobs)
Uses: SendGrid API
```

**Example**:
```python
agent = EmailAgent()

success = agent.send_match_notification(
    alert=AdoptionAlert(
        id=123,
        user_email="user@example.com",
        profile=CatProfile(...)
    ),
    matches=[CatMatch(...), CatMatch(...)]
)

# Generates HTML email:
# Subject: "Tuxedo Link: 2 New Cat Matches!"
# Body:
#   - Cat cards with photos
#   - Match scores and explanations
#   - Links back to detail pages
#
# Returns: True if sent successfully
```

---

## Database Layer

**File**: `database/manager.py`  
**Purpose**: All database operations (SQLite)

### Core Methods

#### 1. `cache_cat()`

**Purpose**: Store cat data with image embedding in cache.

**Signature**:
```python
def cache_cat(
    self, 
    cat: Cat, 
    image_embedding: Optional[np.ndarray]
) -> None
```

**Integration**:
```
Called by: PlanningAgent.deduplicate_and_cache()
Stores:
  → Full cat JSON
  → Image embedding (BLOB)
  → Metadata for filtering
```

**Example**:
```python
cat = Cat(id="pf_123", name="Fluffy", ...)
embedding = np.array([0.1, 0.2, ...])  # 512 dimensions

db.cache_cat(cat, embedding)

# Database entry created:
# id: "pf_123"
# name: "Fluffy"
# cat_json: "{...full cat data...}"
# image_embedding: <binary blob>
# fingerprint: "happypaws_persian_adult_female"
# is_duplicate: 0
# fetched_at: 2024-10-27 10:30:00
```

---

#### 2. `get_cats_by_fingerprint()`

**Purpose**: Find cached cats with matching fingerprint.

**Signature**:
```python
def get_cats_by_fingerprint(self, fingerprint: str) -> List[Cat]
```

**Integration**:
```
Called by: DeduplicationAgent.deduplicate()
```

**Example**:
```python
cats = db.get_cats_by_fingerprint("happypaws_persian_adult_female")

# Returns all cached cats with this fingerprint
# Used to check for duplicates across sources
```

---

#### 3. `mark_as_duplicate()`

**Purpose**: Mark a cat as duplicate of another.

**Signature**:
```python
def mark_as_duplicate(self, duplicate_id: str, original_id: str) -> None
```

**Example**:
```python
# Found that pf_123 and rg_456 are same cat
db.mark_as_duplicate(
    duplicate_id="rg_456",
    original_id="pf_123"
)

# Database updated:
# UPDATE cats_cache
# SET is_duplicate=1, duplicate_of='pf_123'
# WHERE id='rg_456'
```

---

#### 4. `get_image_embedding()`

**Purpose**: Retrieve cached image embedding for a cat.

**Signature**:
```python
def get_image_embedding(self, cat_id: str) -> Optional[np.ndarray]
```

**Returns**:
- NumPy array if cached, None otherwise

**Example**:
```python
embedding = db.get_image_embedding("pf_123")
# Returns: np.array([0.1, 0.2, ...]) or None
```

---

#### 5. `create_user()` / `get_user_by_email()`

**Purpose**: User account management.

**Example**:
```python
# Create user
user_id = db.create_user(
    email="user@example.com",
    password_hash="$2b$12$..."
)

# Retrieve user
user = db.get_user_by_email("user@example.com")
# Returns: User(id=1, email="...", password_hash="...")
```

---

#### 6. `create_alert()` / `get_user_alerts()`

**Purpose**: Manage email alert subscriptions.

**Example**:
```python
# Create alert
alert_id = db.create_alert(
    AdoptionAlert(
        user_id=1,
        user_email="user@example.com",
        profile=CatProfile(...),
        frequency="daily"
    )
)

# Get user's alerts
alerts = db.get_user_alerts(user_id=1)
# Returns: [AdoptionAlert(...), ...]
```

---

## Vector Database

**File**: `setup_vectordb.py`  
**Purpose**: ChromaDB operations for semantic search

### Core Class: `VectorDBManager`

#### 1. `add_cats()`

**Purpose**: Add cat embeddings to vector database.

**Signature**:
```python
def add_cats(self, cats: List[Cat]) -> None
```

**Integration**:
```
Called by: PlanningAgent.update_vector_db()
Uses: SentenceTransformer for embeddings
```

**Example**:
```python
vdb = VectorDBManager("cat_vectorstore")

cats = [
    Cat(id="pf_1", name="Fluffy", description="Friendly lap cat"),
    Cat(id="pf_2", name="Max", description="Playful and energetic")
]

vdb.add_cats(cats)

# Process:
# 1. Generate embeddings from description - "Friendly lap cat" 
# 2. Store in ChromaDB with metadata
# 3. Available for vector search
```

---

#### 2. `search()`

**Purpose**: Semantic search for similar cats.

**Signature**:
```python
def search(
    self, 
    query: str, 
    n_results: int = 100
) -> List[Dict]
```

**Parameters**:
- `query`: Natural language description
- `n_results`: Number of results to return

**Returns**:
- List of cat IDs and metadata

**Integration**:
```
Called by: MatchingAgent.search()
```

**Example**:
```python
results = vdb.search(
    query="friendly lap cat good with kids",
    n_results=50
)

# Returns:
# [
#   {
#     'id': 'pf_123',
#     'distance': 0.12,  # Lower = more similar
#     'metadata': {
#       'name': 'Fluffy',
#       'breed': 'Persian',
#       'age': 'young'
#     }
#   },
#   ...
# ]

# Sorted by similarity (semantic matching)
```

---

## Models Layer

**File**: `models/cats.py`  
**Purpose**: Pydantic data models

### Key Models

#### 1. `Cat`

**Purpose**: Represent a cat available for adoption.

**Fields**:
```python
Cat(
    id: str                              # "petfinder_12345"
    name: str                            # "Fluffy"
    breed: str                           # "Persian"
    age: str                             # "young", "adult", "senior"
    gender: str                          # "male", "female"
    size: str                            # "small", "medium", "large"
    description: str                     # Full description
    organization_name: str               # "Happy Paws Rescue"
    city: str                            # "Brooklyn"
    state: str                           # "NY"
    source: str                          # "petfinder", "rescuegroups"
    url: str                             # Direct link to listing
    primary_photo: Optional[str]         # Photo URL
    good_with_children: Optional[bool]
    good_with_dogs: Optional[bool]
    good_with_cats: Optional[bool]
    adoption_fee: Optional[float]
    fingerprint: Optional[str]           # For deduplication
    fetched_at: datetime
)
```

---

#### 2. `CatProfile`

**Purpose**: User's search preferences.

**Fields**:
```python
CatProfile(
    user_location: Optional[str]         # "10001" or "Brooklyn, NY"
    max_distance: int = 100              # Miles
    personality_description: str = ""    # "friendly lap cat"
    age_range: Optional[List[str]]       # ["young", "adult"]
    size: Optional[List[str]]            # ["small", "medium"]
    good_with_children: Optional[bool]
    good_with_dogs: Optional[bool]
    good_with_cats: Optional[bool]
    gender_preference: Optional[str]
)
```

---

#### 3. `CatMatch`

**Purpose**: A matched cat with scoring details.

**Fields**:
```python
CatMatch(
    cat: Cat                             # The matched cat
    match_score: float                   # 0.0-1.0 overall score
    vector_similarity: float             # Semantic similarity
    attribute_match_score: float         # Metadata match
    explanation: str                     # Human-readable why
    matching_attributes: List[str]       # What matched
    missing_attributes: List[str]        # What didn't match
)
```

---

#### 4. `SearchResult`

**Purpose**: Complete search results returned to UI.

**Fields**:
```python
SearchResult(
    matches: List[CatMatch]              # Top ranked matches
    total_found: int                     # Before filtering
    search_profile: CatProfile           # What was searched
    search_time: float                   # Seconds
    sources_queried: List[str]           # APIs used
    duplicates_removed: int              # Dedup count
)
```

---

## Utilities

### Deduplication Utils

**File**: `utils/deduplication.py`

#### 1. `create_fingerprint()`

**Purpose**: Generate unique fingerprint from stable attributes.

**Signature**:
```python
def create_fingerprint(cat: Cat) -> str
```

**Returns**:
- MD5 hash of normalized attributes

**Example**:
```python
# Same attributes = same fingerprint
cat = Cat(
    organization_name="Happy Paws Rescue",
    breed="Persian",
    age="adult",
    gender="female"
)

fingerprint = create_fingerprint(cat)
# Returns: "a5d2f8e3c1b4d6a7"
```

---

#### 2. `calculate_levenshtein_similarity()`

**Purpose**: Calculate text similarity (0.0-1.0).

**Signature**:
```python
def calculate_levenshtein_similarity(str1: str, str2: str) -> float
```

**Example**:
```python
sim = calculate_levenshtein_similarity(
    "Fluffy the friendly cat",
    "Fluffy - a friendly feline"
)
# Returns: 0.78 (78% similar)
```

---

#### 3. `calculate_composite_score()`

**Purpose**: Combine multiple similarity scores with weights.

**Signature**:
```python
def calculate_composite_score(
    name_similarity: float,
    description_similarity: float,
    image_similarity: float,
    name_weight: float = 0.4,
    description_weight: float = 0.3,
    image_weight: float = 0.3
) -> float
```

**Example**:
```python
score = calculate_composite_score(
    name_similarity=0.9,
    description_similarity=0.8,
    image_similarity=0.95
)
# Returns: 0.88
# Calculation: 0.9*0.4 + 0.8*0.3 + 0.95*0.3 = 0.885
```

---

### Image Utils

**File**: `utils/image_utils.py`

#### `get_image_embedding()`

**Purpose**: Generate CLIP embedding for image URL.

**Signature**:
```python
def get_image_embedding(image_url: str) -> Optional[np.ndarray]
```

**Returns**:
- 512-dimensional embedding or None

**Integration**:
```
Called by: DeduplicationAgent.deduplicate()
Uses: CLIP model (ViT-B/32)
```

**Example**:
```python
embedding = get_image_embedding("https://example.com/cat.jpg")
# Returns: np.array([0.23, -0.15, 0.87, ...])  # 512 dims

# Can then compare:
similarity = cosine_similarity(embedding1, embedding2)
# Returns: 0.95 (very similar images)
```

---

## Modal Services

Tuxedo Link uses Modal for serverless cloud deployment with a hybrid architecture.

### Architecture Overview

#### Production Mode (Modal)

```
┌─────────────────┐
│   Local UI      │  Gradio interface
│   (app.py)      │  - Lightweight, no ML models
└────────┬────────┘  - Fast startup
         │
         │ modal.Function.from_name().remote()
         ↓
┌─────────────────┐
│   Modal API     │  Main backend (modal_api.py)
│   Cloud         │  - Profile extraction
│                 │  - Cat search
│                 │  - Alert management
└────────┬────────┘
         │
         ├──→ Database (Modal volume)
         ├──→ Vector DB (Modal volume)
         └──→ Email providers
         
┌─────────────────┐
│   Modal Jobs    │  Scheduled tasks (scheduled_search.py)
│   Cloud         │  - Daily alerts (9 AM)
│                 │  - Weekly alerts (Mon 9 AM)
│                 │  - Cleanup (Sun 2 AM)
└─────────────────┘
```

#### Local Mode (Development)

```
┌─────────────────┐
│   Local All     │  Everything runs locally
│   (app.py)      │  - Full framework
│                 │  - Local DB & vector DB
│                 │  - No Modal
└─────────────────┘
```

### Modal Files

**File Locations**: Both files are at project **root** (not in subdirectory) for Modal's auto-discovery to work.

#### 1. `modal_api.py` - Main Backend API

**Purpose**: Expose core functionality as Modal functions for UI consumption.

**Deployed as**: `tuxedo-link-api` app on Modal

**Functions**:

##### `extract_profile(user_text: str)`

Extract CatProfile from natural language.

```python
@app.function(secrets=[modal.Secret.from_name("tuxedo-link-secrets")])
def extract_profile(user_text: str) -> Dict[str, Any]:
    """Extract profile via GPT-4 on Modal."""
    profile_agent = ProfileAgent()
    conversation = [{"role": "user", "content": user_text}]
    profile = profile_agent.extract_profile(conversation)
    return {"success": True, "profile": profile.model_dump()}
```

**Called by**: `app.py:extract_profile_from_text()` in production mode

```python
# In app.py (production mode)
extract_profile_func = modal.Function.from_name("tuxedo-link-api", "extract_profile")
result = extract_profile_func.remote(user_input)
```

---

##### `search_cats(profile_dict: Dict, use_cache: bool)`

Execute complete search pipeline on Modal.

```python
@app.function(
    secrets=[modal.Secret.from_name("tuxedo-link-secrets")],
    volumes={"/data": volume},
    timeout=300
)
def search_cats(profile_dict: Dict[str, Any], use_cache: bool = False) -> Dict[str, Any]:
    """Run search on Modal cloud."""
    framework = TuxedoLinkFramework()
    profile = CatProfile(**profile_dict)
    result = framework.search(profile, use_cache=use_cache)
    
    return {
        "success": True,
        "matches": [
            {
                "cat": m.cat.model_dump(),
                "match_score": m.match_score,
                "vector_similarity": m.vector_similarity,
                "attribute_match_score": m.attribute_match_score,
                "explanation": m.explanation,
                "matching_attributes": m.matching_attributes,
                "missing_attributes": m.missing_attributes,
            }
            for m in result.matches
        ],
        "total_found": result.total_found,
        "duplicates_removed": result.duplicates_removed,
        "sources_queried": result.sources_queried,
        "timestamp": datetime.now().isoformat(),
    }
```

**Called by**: `app.py:extract_profile_from_text()` in production mode

```python
# In app.py (production mode)
search_cats_func = modal.Function.from_name("tuxedo-link-api", "search_cats")
search_result = search_cats_func.remote(profile.model_dump(), use_cache=use_cache)
```

---

##### `create_alert_and_notify()`, `get_alerts()`, `update_alert()`, `delete_alert()`

Alert management functions exposed via Modal.

**Called by**: `app.py` alert management UI in production mode

---

##### `send_immediate_notification(alert_id: int)`

Trigger immediate email notification for an alert.

```python
@app.function(
    secrets=[modal.Secret.from_name("tuxedo-link-secrets")],
    volumes={"/data": volume}
)
def send_immediate_notification(alert_id: int) -> Dict[str, Any]:
    """Send immediate notification on Modal."""
    # Get alert, run search, send email
    # ...
```

**Called by**: `app.py:save_alert()` when frequency is "Immediately" in production mode

---

#### 2. `scheduled_search.py` - Background Jobs

**Purpose**: Scheduled tasks for alert processing and cleanup.

**Deployed as**: `tuxedo-link-scheduled-search` app on Modal

**Functions**:

##### `run_scheduled_searches()`

**Purpose**: Process all active alerts and send notifications.

**Signature**:
```python
@app.function(
    schedule=modal.Cron("0 9 * * *"),  # Daily 9 AM UTC
    secrets=[modal.Secret.from_name("tuxedo-link-secrets")],
    volumes={"/data": volume}
)
def run_scheduled_searches() -> None
```

**Integration**:
```
Called by:
  → daily_search_job() (cron: daily at 9 AM)
  → weekly_search_job() (cron: Monday at 9 AM)
```

**Flow**:
```python
# Executed on Modal cloud
run_scheduled_searches()

# Process:
# 1. Load all active alerts from database
# 2. For each alert:
#    a. Run cat search with saved profile
#    b. Filter out cats already seen
#    c. If new matches found:
#       - Send email notification
#       - Update last_sent timestamp
#       - Store match IDs to avoid duplicates
# 3. Log completion
```

**Example**:
```
[2024-10-29 09:00:00] Starting scheduled search job
Found 15 active alerts

Processing alert 1 for user@example.com
  Found 3 new matches for alert 1
  Email sent successfully for alert 1

Processing alert 2 for other@example.com
  No new matches for alert 2

...

[2024-10-29 09:05:32] Scheduled search job completed
```

---

##### `cleanup_old_data()`

**Purpose**: Remove cached cats older than N days.

**Signature**:
```python
@app.function(
    schedule=modal.Cron("0 2 * * 0"),  # Sunday 2 AM UTC
    volumes={"/data": volume}
)
def cleanup_old_data(days: int = 30) -> Dict[str, Any]
```

**Integration**:
```
Called by: weekly_cleanup_job() (Sunday 2 AM)
```

**Example**:
```python
stats = cleanup_old_data(days=30)

# Removes:
# - Cats not seen in 30+ days
# - Embeddings from ChromaDB
# - Duplicate markers

# Returns:
# {
#   'removed': 145,
#   'kept': 250,
#   'vector_db_size': 250
# }
```

---

### Modal Image Configuration

Both Modal files use a carefully configured image with compatible package versions:

```python
from pathlib import Path
import modal

project_dir = Path(__file__).parent

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "openai",
        "chromadb",
        "requests",
        "sentence-transformers==2.5.1",  # Compatible with torch 2.2.2
        "transformers==4.38.0",          # Compatible with torch 2.2.2
        "Pillow",
        "python-dotenv",
        "pydantic",
        "geopy",
        "pyyaml",
        "python-levenshtein",
        "open-clip-torch==2.24.0",       # Compatible with torch 2.2.2
    )
    .apt_install("git")
    .run_commands(
        "pip install torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu",
        "pip install numpy==1.26.4",
    )
    # Add only necessary source directories
    .add_local_dir(str(project_dir / "models"), remote_path="/root/models")
    .add_local_dir(str(project_dir / "agents"), remote_path="/root/agents")
    .add_local_dir(str(project_dir / "database"), remote_path="/root/database")
    .add_local_dir(str(project_dir / "utils"), remote_path="/root/utils")
    # Add standalone Python files
    .add_local_file(str(project_dir / "cat_adoption_framework.py"), remote_path="/root/cat_adoption_framework.py")
    .add_local_file(str(project_dir / "setup_vectordb.py"), remote_path="/root/setup_vectordb.py")
    .add_local_file(str(project_dir / "setup_metadata_vectordb.py"), remote_path="/root/setup_metadata_vectordb.py")
    # Add config file
    .add_local_file(str(project_dir / "config.yaml"), remote_path="/root/config.yaml")
)
```

**Critical Points**:
1. ✅ Modal files at project root for auto-discovery
2. ✅ Top-level imports (not inside functions)
3. ✅ Explicit `add_local_dir()` for each source directory
4. ✅ Compatible package versions (torch 2.2.2, transformers 4.38.0, etc.)
5. ✅ Only necessary files added (not `.venv`, `cat_vectorstore`, etc.)

---

### UI Integration with Modal

**File**: `app.py`

The UI uses conditional logic based on `is_production()` to either call Modal or use local framework:

```python
from utils.config import is_production

if not is_production():
    # LOCAL MODE: Import and initialize heavy components
    from cat_adoption_framework import TuxedoLinkFramework
    from agents.profile_agent import ProfileAgent

    framework = TuxedoLinkFramework()
    profile_agent = ProfileAgent()
    print("✓ Running in LOCAL mode - using local components")
else:
    # PRODUCTION MODE: Don't import heavy components - use Modal API
    print("✓ Running in PRODUCTION mode - using Modal API")
```

**Search Flow in Production**:

```python
def extract_profile_from_text(user_input: str, use_cache: bool = False):
    if is_production():
        # PRODUCTION: Call Modal API
        import modal
        
        # Extract profile via Modal
        extract_profile_func = modal.Function.from_name("tuxedo-link-api", "extract_profile")
        profile_result = extract_profile_func.remote(user_input)
        profile = CatProfile(**profile_result["profile"])
        
        # Search via Modal
        search_cats_func = modal.Function.from_name("tuxedo-link-api", "search_cats")
        search_result = search_cats_func.remote(profile.model_dump(), use_cache=use_cache)
        
        # Reconstruct matches from Modal response
        current_matches = [
            CatMatch(
                cat=Cat(**m["cat"]),
                match_score=m["match_score"],
                vector_similarity=m["vector_similarity"],
                attribute_match_score=m["attribute_match_score"],
                explanation=m["explanation"],
                matching_attributes=m.get("matching_attributes", []),
                missing_attributes=m.get("missing_attributes", [])
            )
            for m in search_result["matches"]
        ]
    else:
        # LOCAL: Use local framework
        profile = profile_agent.extract_profile([{"role": "user", "content": user_input}])
        result = framework.search(profile, use_cache=use_cache)
        current_matches = result.matches
    
    # Rest of function same for both modes
    return chat_history, results_html, profile_json
```

---

### Deployment Process

**See**: `docs/MODAL_DEPLOYMENT.md` for complete deployment guide

**Quick Deploy**:
```bash
# 1. Set production mode in config.yaml
deployment:
  mode: production

# 2. Deploy Modal API
modal deploy modal_api.py

# 3. Deploy scheduled jobs
modal deploy scheduled_search.py

# 4. Run UI locally (connects to Modal)
./run.sh
```

---

## Complete User Journey Examples

### Example 1: First-Time Search

**User Action**: Types "friendly kitten in NYC, good with kids"

**System Flow**:

```python
# 1. UI receives input
user_text = "friendly kitten in NYC, good with kids"

# 2. Convert to conversation format & extract profile
profile_agent = ProfileAgent()
conversation = [{"role": "user", "content": user_text}]
profile = profile_agent.extract_profile(conversation)
# → OpenAI GPT-4 API call (with conversation format)
# ← CatProfile(location="NYC", age_range=["kitten"], good_with_children=True)

# 3. Execute search
framework = TuxedoLinkFramework()
result = framework.search(profile, use_cache=False)

# 4. Planning agent orchestrates
planner = PlanningAgent()

# 4a. Fetch from APIs (parallel)
petfinder_cats = PetfinderAgent().search_cats(
    location="NYC",
    age="kitten",
    good_with_children=True
)  # Returns 45 cats

rescuegroups_cats = RescueGroupsAgent().search_cats(
    location="NYC",
    age="kitten"
)  # Returns 38 cats

# Total: 83 cats

# 4b. Deduplicate
dedup_agent = DeduplicationAgent()
unique_cats = dedup_agent.deduplicate(cats)
# Finds 8 duplicates (same cat on both platforms)
# Unique: 75 cats

# 4c. Cache with embeddings
for cat in unique_cats:
    db.cache_cat(cat, get_image_embedding(cat.primary_photo))
    
# 4d. Add to vector DB
vector_db.add_cats(unique_cats)

# 4e. Match and rank
matching_agent = MatchingAgent()
matches = matching_agent.search(profile, top_k=20)

# Vector search finds: 50 semantically similar
# Metadata filter: 32 meet hard constraints
# Hybrid scoring: Rank all 32
# Return top 20

# 5. Format and display
html = build_results_grid(matches)

# 6. Return to user (OpenAI messages format)
return (
    chat_history=[
        {"role": "user", "content": "friendly kitten in NYC, good with kids"},
        {"role": "assistant", "content": "✅ Got it! Searching for...\n\n✨ Found 20 cats!"}
    ],
    results_html=html,
    profile_display='{"user_location": "NYC", "age_range": ["kitten"], ...}'
)
```

**Result**: User sees 20 cat cards with photos, match scores, and explanations.

**Note**: Chat history now uses OpenAI messages format (Gradio `type="messages"`) instead of deprecated tuples format.

---

### Example 2: Cached Search (Developer Mode)

**User Action**: Same search with "Use Cache" enabled

**System Flow**:

```python
# 1-2. Same as above (extract profile)

# 3. Execute search with cache
result = framework.search(profile, use_cache=True)

# 4. Planning agent uses cache
cats = db.get_all_cached_cats(exclude_duplicates=True)
# Returns: 75 cats (from previous search)

# Skip API calls, deduplication, caching

# 4a. Match and rank (same as before)
matches = matching_agent.search(profile, top_k=20)

# 5-6. Same as above (format and display)
```

**Result**: 
- Much faster (0.2s vs 13s)
- No API calls (preserves rate limits)
- Same quality results

---

### Example 3: Email Alert Flow

**User Action**: Saves search as daily alert

**Initial Setup**:
```python
# 1. User registers
user_id = db.create_user(email="user@example.com", password_hash="...")

# 2. User creates alert
alert = AdoptionAlert(
    user_id=user_id,
    user_email="user@example.com",
    profile=CatProfile(...),  # Their search preferences
    frequency="daily",
    active=True
)
alert_id = db.create_alert(alert)
```

**Daily Scheduled Job** (Modal, 9 AM):
```python
# Runs on Modal cloud
run_scheduled_searches()

# 1. Load alerts
alerts = db.get_active_alerts()
# Returns: [AdoptionAlert(...), ...]

# 2. For user's alert
alert = alerts[0]  # user@example.com

# 3. Run search
result = framework.search(alert.profile)
# Returns: 18 matches

# 4. Filter new matches
last_seen_ids = alert.last_match_ids  # ["pf_1", "pf_2", ...]
new_matches = [
    m for m in result.matches 
    if m.cat.id not in last_seen_ids
]
# New matches: 3 cats

# 5. Send email
email_agent = EmailAgent()
email_agent.send_match_notification(alert, new_matches)

# Email content:
# Subject: "Tuxedo Link: 3 New Cat Matches!"
# Body:
#   - Cat 1: Fluffy (85% match)
#     [Photo]
#     Great personality match, loves children
#     [View Details →]
#
#   - Cat 2: Max (82% match)
#     ...

# 6. Update alert
db.update_alert(
    alert_id=alert.id,
    last_sent=datetime.now(),
    last_match_ids=[m.cat.id for m in new_matches]
)
```

**Result**: User receives email with 3 new cats, won't see them again tomorrow.

---

### Example 4: Deduplication in Action

**Scenario**: Same cat listed on Petfinder AND RescueGroups

**Cat on Petfinder**:
```python
cat1 = Cat(
    id="petfinder_12345",
    name="Fluffy",
    breed="Persian",
    age="adult",
    gender="female",
    organization_name="Happy Paws Rescue",
    description="Friendly lap cat who loves cuddles",
    primary_photo="https://petfinder.com/photos/cat1.jpg"
)
```

**Same Cat on RescueGroups**:
```python
cat2 = Cat(
    id="rescuegroups_67890",
    name="Fluffy (Happy Paws)",
    breed="Persian",
    age="adult",
    gender="female",
    organization_name="Happy Paws Rescue",
    description="Sweet lap cat, loves to cuddle",
    primary_photo="https://rescuegroups.org/photos/cat2.jpg"
)
```

**Deduplication Process**:
```python
dedup_agent = DeduplicationAgent(db)
unique = dedup_agent.deduplicate([cat1, cat2])

# Step 1: Fingerprint
fp1 = create_fingerprint(cat1)
# → "happypaws_persian_adult_female"
fp2 = create_fingerprint(cat2)
# → "happypaws_persian_adult_female"
# ✓ MATCH! Likely duplicate

# Step 2: Text similarity
name_sim = calculate_levenshtein_similarity(
    "Fluffy",
    "Fluffy (Happy Paws)"
)
# → 0.73

desc_sim = calculate_levenshtein_similarity(
    "Friendly lap cat who loves cuddles",
    "Sweet lap cat, loves to cuddle"
)
# → 0.82

# Step 3: Image similarity
embed1 = get_image_embedding(cat1.primary_photo)
embed2 = get_image_embedding(cat2.primary_photo)
img_sim = cosine_similarity(embed1, embed2)
# → 0.94 (very similar - probably same photo)

# Step 4: Composite score
score = calculate_composite_score(
    name_similarity=0.73,
    description_similarity=0.82,
    image_similarity=0.94
)
# → 0.82 (82% - above 75% threshold)

# Step 5: Mark as duplicate
db.mark_as_duplicate(
    duplicate_id="rescuegroups_67890",
    original_id="petfinder_12345"
)

# Result: Only cat1 returned to user
```

**Result**: User sees Fluffy once, not twice.

---

## Summary of Key Integration Points

### Data Flow Chain

1. **User Input** → `app.py:extract_profile_from_text()`
2. **Profile Extraction** → `profile_agent.py:extract_profile()`
3. **Search Orchestration** → `planning_agent.py:search()`
4. **API Fetching** → `petfinder_agent.py:search_cats()` + `rescuegroups_agent.py:search_cats()`
5. **Deduplication** → `deduplication_agent.py:deduplicate()`
6. **Caching** → `manager.py:cache_cat()`
7. **Embedding** → `setup_vectordb.py:add_cats()`
8. **Matching** → `matching_agent.py:search()`
9. **Display** → `app.py:build_results_grid()`

### Cross-Cutting Functionality

**Logging**: Every agent uses `agent.py:log()` with color coding

**Rate Limiting**: `petfinder_agent.py:_rate_limit()` and `rescuegroups_agent.py:_rate_limit()`

**Error Handling**: Try/except blocks at agent level, graceful degradation

**Caching**: Two-level (SQLite + ChromaDB) for speed and quality

**Timing**: `@timed` decorator tracks performance

