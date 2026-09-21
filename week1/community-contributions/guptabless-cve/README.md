# CVE Details Fetcher

Fetch CVE details from NIST NVD API and optionally enhance with local LLM analysis.

## Quick Start

### Step 1: NVD Fetch & Parse
```python
CVE_TO_FETCH = "CVE-2024-38063"
result = fetch_and_parse_cve(CVE_TO_FETCH)
```

### Step 2: Ollama Analysis (Optional)
```python
if result.get('error') is None:
    result = ollama_security_report(result)
```

### Step 3: View Results
```python
print(json.dumps(result, indent=2, default=str))
```

## Setup

### Without Ollama (Basic)
No setup needed! Just run the notebook.

### With Ollama (Enhanced)
```bash
# 1. Install Ollama
https://ollama.ai

# 2. Pull lightweight model
ollama pull llama3.2

# 3. Start Ollama
ollama serve

# 4. In notebook, enable:
USE_OLLAMA = True
OLLAMA_MODEL = "llama3.2"
```

## Configuration

Edit Cell 3:
```python
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
OLLAMA_API = "http://localhost:11434/v1/chat/completions"
OLLAMA_MODEL = "llama3.2"  # lightweight
USE_OLLAMA = False  # set True once Ollama is running
```

## Output Example

```json
{
  "success": true,
  "cve_id": "CVE-2024-38063",
  "description": "Vulnerability description...",
  "published": "2024-08-13T00:00:00Z",
  "cvss_v3": {
    "score": 9.8,
    "severity": "CRITICAL"
  },
  "cvss_v2": {
    "score": 10.0
  },
  "cwe_list": ["CWE-89"],
  "affected_products": ["cpe:2.3:a:vendor:product:*:*:*:*:*:*:*:*"],
  "references": ["https://nvd.nist.gov/..."],
  "stats": {
    "total_products": 45,
    "total_cwes": 2,
    "total_refs": 8
  },
  "ollama_analysis": {
    "model": "llama3.2",
    "report": "This is a critical SQL injection vulnerability affecting..."
  }
}
```

## Notebooks Functions

### `fetch_and_parse_cve(cve_id: str)`
Fetch CVE from NVD and extract:
- CVSS scores (v2 & v3)
- CWE (weaknesses)
- Affected products
- References

### `ollama_security_report(cve_data: dict)`
Generate security report using local LLM:
- Checks if Ollama is available
- Generates risk assessment
- Falls back gracefully if unavailable

### `test_cve_fetcher()`
Automated tests, each checked against an expected pass/fail outcome:
- Valid CVE with Ollama
- Valid CVE without Ollama (Log4Shell)
- Lowercase CVE id is normalized
- Invalid format is rejected
- Non-existent CVE is rejected
- Empty input is rejected

## Example CVEs

```python
"CVE-2024-38063"   # Recent critical
"CVE-2024-1234"    # Valid format
"CVE-2023-44487"   # HTTP/2 Rapid Reset
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid CVE format | Wrong format | Use: CVE-YYYY-XXXXX |
| Not found in NVD | Non-existent CVE | Check CVE ID |
| Timeout | Network slow | Check internet connection |
| Ollama unavailable | Not running | Install & start Ollama |

## Features

- Free NVD API (no API key)
- Lightweight model (llama3.2)
- Built-in test cases
- Graceful fallback (works without Ollama)
- JSON output
- Local privacy (no cloud APIs)

## Resources

- [NVD API Docs](https://nvd.nist.gov/developers/vulnerabilities)
- [Ollama](https://ollama.ai)
- [Llama3.2](https://ollama.ai/library/llama3.2)
