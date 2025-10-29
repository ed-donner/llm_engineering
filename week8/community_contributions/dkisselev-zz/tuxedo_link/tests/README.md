# 🧪 Testing Guide

## Test Overview

**Status**: ✅ **92/92 tests passing** (100%)

The test suite includes:
- **81 unit tests** - Models, database, deduplication, email providers, semantic matching
- **11 integration tests** - Search pipeline, alerts, app functionality, color/breed normalization
- **4 manual test scripts** - Cache testing, email sending, semantic matching, framework testing

---

## Unit Tests (81 tests ✅)

Unit tests validate individual components in isolation.

### Test Data Models
```bash
pytest tests/unit/test_models.py -v
```

**Tests**:
- Cat model validation
- CatProfile model validation
- CatMatch model validation
- AdoptionAlert model validation
- SearchResult model validation
- Field requirements and defaults
- JSON serialization

### Test Database Operations
```bash
pytest tests/unit/test_database.py -v
```

**Tests**:
- Database initialization
- Cat caching with fingerprints
- Duplicate marking
- Image embedding storage
- Alert CRUD operations
- Query filtering
- Statistics retrieval

### Test Deduplication Logic
```bash
pytest tests/unit/test_deduplication.py -v
```

**Tests**:
- Fingerprint creation
- Levenshtein similarity calculation
- Composite score calculation
- Three-tier deduplication pipeline
- Image embedding comparison

### Test Email Providers
```bash
pytest tests/unit/test_email_providers.py -v
```

**Tests**:
- Mailgun provider initialization
- Mailgun email sending
- SendGrid stub behavior
- Provider factory
- Configuration loading
- Error handling

### Test Metadata Vector Database
```bash
pytest tests/unit/test_metadata_vectordb.py -v
```

**Tests** (11):
- Vector DB initialization
- Color indexing from multiple sources
- Breed indexing from multiple sources
- Semantic search for colors
- Semantic search for breeds
- Fuzzy matching with typos
- Multi-source filtering
- Empty search handling
- N-results parameter
- Statistics retrieval

### Test Color Mapping
```bash
pytest tests/unit/test_color_mapping.py -v
```

**Tests** (15):
- Dictionary matching for common terms (tuxedo, orange, gray)
- Multiple color normalization
- Exact match fallback
- Substring match fallback
- Vector DB fuzzy matching
- Typo handling
- Dictionary priority over vector search
- Case-insensitive matching
- Whitespace handling
- Empty input handling
- Color suggestions
- All dictionary mappings validation

### Test Breed Mapping
```bash
pytest tests/unit/test_breed_mapping.py -v
```

**Tests** (20):
- Dictionary matching for common breeds (Maine Coon, Ragdoll, Sphynx)
- Typo correction ("main coon" → "Maine Coon")
- Mixed breed handling
- Exact match fallback
- Substring match fallback
- Vector DB fuzzy matching
- Dictionary priority
- Case-insensitive matching
- DSH/DMH/DLH abbreviations
- Tabby/tuxedo pattern recognition
- Norwegian Forest Cat variations
- Similarity threshold testing
- Breed suggestions
- Whitespace handling
- All dictionary mappings validation

---

## Integration Tests (11 tests ✅)

Integration tests validate end-to-end workflows.

### Test Search Pipeline
```bash
pytest tests/integration/test_search_pipeline.py -v
```

**Tests**:
- Complete search flow (API → dedup → cache → match → results)
- Cache mode functionality
- Deduplication integration
- Hybrid matching
- API failure handling
- Vector DB updates
- Statistics tracking

### Test Alerts System
```bash
pytest tests/integration/test_alerts.py -v
```

**Tests**:
- Alert creation and retrieval
- Email-based alert queries
- Alert updates (frequency, status)
- Alert deletion
- Immediate notifications (production mode)
- Local vs production behavior
- UI integration

### Test App Functionality
```bash
pytest tests/integration/test_app.py -v
```

**Tests**:
- Profile extraction from UI
- Search result formatting
- Alert management UI
- Email validation
- Error handling

### Test Color and Breed Normalization
```bash
pytest tests/integration/test_color_breed_normalization.py -v
```

**Tests**:
- Tuxedo color normalization in search flow
- Multiple colors normalization
- Breed normalization (Maine Coon typo handling)
- Fuzzy matching with vector DB
- Combined colors and breeds in search
- RescueGroups API normalization
- Empty preferences handling
- Invalid color/breed graceful handling

---

## Manual Test Scripts

These scripts are for manual testing with real APIs and data.

### Test Cache and Deduplication
```bash
python tests/manual/test_cache_and_dedup.py
```

**Purpose**: Verify cache mode and deduplication with real data

**What it does**:
1. Runs a search without cache (fetches from APIs)
2. Displays statistics (cats found, duplicates removed, cache size)
3. Runs same search with cache (uses cached data)
4. Compares performance and results
5. Shows image embedding deduplication in action

### Test Email Sending
```bash
python tests/manual/test_email_sending.py
```

**Purpose**: Send test emails via configured provider

**What it does**:
1. Sends welcome email
2. Sends match notification email with sample data
3. Verifies HTML rendering and provider integration

**Requirements**: Valid MAILGUN_API_KEY or SENDGRID_API_KEY in `.env`

### Test Semantic Color/Breed Matching
```bash
python scripts/test_semantic_matching.py
```

**Purpose**: Verify 3-tier color and breed matching system

**What it does**:
1. Tests color mapping with and without vector DB
2. Tests breed mapping with and without vector DB
3. Demonstrates typo handling ("tuxado" → "tuxedo", "ragdol" → "Ragdoll")
4. Shows dictionary vs vector vs fallback matching
5. Displays similarity scores for fuzzy matches

**What you'll see**:
- ✅ Dictionary matches (instant)
- ✅ Vector DB fuzzy matches (with similarity scores)
- ✅ Typo correction in action
- ✅ 3-tier strategy demonstration

### Test Framework Directly
```bash
python cat_adoption_framework.py
```

**Purpose**: Run framework end-to-end test

**What it does**:
1. Initializes framework
2. Creates sample profile
3. Executes search
4. Displays top matches
5. Shows statistics

---

## Test Configuration

### Fixtures

Common test fixtures are defined in `tests/conftest.py`:

- `temp_db` - Temporary database for testing
- `temp_vectordb` - Temporary vector store
- `sample_cat` - Sample cat object
- `sample_profile` - Sample search profile
- `mock_framework` - Mocked framework for unit tests

### Environment

Tests use separate databases to avoid affecting production data:
- `test_tuxedo_link.db` - Test database (auto-deleted)
- `test_vectorstore` - Test vector store (auto-deleted)

### Mocking

External APIs are mocked in unit tests:
- Petfinder API calls
- RescueGroups API calls
- Email provider calls
- Modal remote functions

Integration tests can use real APIs (set `SKIP_API_TESTS=false` in environment).

---

**Need help?** Check the [TECHNICAL_REFERENCE.md](../docs/TECHNICAL_REFERENCE.md) for detailed function documentation.

