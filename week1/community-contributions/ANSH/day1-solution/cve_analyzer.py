import requests
import ollama
from typing import Dict, Any, Optional

class CVESecurityAnalyzer:
    """
    A powerful system to fetch, analyze, and summarize CVE vulnerabilities
    for Secure Development Lifecycle (SDL) integration using local LLMs.
    """
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.nvd_base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        
        # High quality system prompt designed for DevSecOps/SDL Engineers
        self.system_prompt = (
            "You are an Elite Application Security Engineer and DevSecOps Architect. "
            "Your job is to analyze raw CVE data and translate it into a highly actionable, "
            "commercially usable Secure Development Lifecycle (SDL) summary for engineering teams.\n\n"
            "Analyze the vulnerability and format your response in strict Markdown using the following structure:\n"
            "1. **Executive Summary:** A concise 1-2 sentence high-level explanation for management.\n"
            "2. **Technical Threat & Exploitability:** How a threat actor could exploit this, including architectural context.\n"
            "3. **Business Impact:** What happens if this is exploited in production (e.g., data breach, RCE, DoS).\n"
            "4. **Developer Remediation Strategy:** Exact steps developers must take to patch or mitigate this in their codebase/infrastructure.\n"
            "5. **SDL Integration & Prevention:** Specific SAST, DAST, SCA, or code review guidelines to prevent this in the future."
        )

    def fetch_cve_data(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """Fetches raw CVE data from NVD API."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SDL-Analyzer/1.0"}
            response = requests.get(f"{self.nvd_base_url}?cveId={cve_id}", headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("vulnerabilities"):
                print(f"[-] No data found for {cve_id} on NVD.")
                return None
                
            return data["vulnerabilities"][0]["cve"]
        except requests.exceptions.RequestException as e:
            print(f"[-] Error fetching data from NVD API: {e}")
            return None

    def parse_cve_details(self, cve_data: Dict[str, Any]) -> str:
        """Extracts the most important context from the raw NVD JSON."""
        cve_id = cve_data.get("id", "Unknown CVE")
        
        # Extract Description
        descriptions = cve_data.get("descriptions", [])
        english_desc = next((desc["value"] for desc in descriptions if desc["lang"] == "en"), "No description available.")
        
        # Extract Metrics
        metrics = cve_data.get("metrics", {})
        cvss_data = None
        for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            if version in metrics:
                cvss_data = metrics[version][0].get("cvssData", {})
                break
                
        score = cvss_data.get("baseScore", "Unknown") if cvss_data else "Unknown"
        severity = cvss_data.get("baseSeverity", "Unknown") if cvss_data else "Unknown"
        vector = cvss_data.get("vectorString", "Unknown") if cvss_data else "Unknown"

        context = (
            f"Vulnerability: {cve_id}\n"
            f"Severity: {severity} (CVSS Score: {score})\n"
            f"Attack Vector: {vector}\n"
            f"NVD Description: {english_desc}\n"
        )
        return context

    def generate_sdl_report(self, cve_id: str) -> str:
        """The main pipeline: Fetch -> Parse -> Analyze with LLM."""
        print(f"[*] Starting Analysis for {cve_id} using model: {self.model_name}...")
        
        raw_data = self.fetch_cve_data(cve_id)
        if not raw_data:
            return f"Failed to retrieve details for {cve_id}. It might be invalid or NVD is rate-limiting you."

        context_str = self.parse_cve_details(raw_data)
        
        print("[*] Analyzing threat and generating SDL Remediation Plan...")
        user_prompt = f"Please analyze this vulnerability and generate the comprehensive SDL report:\n\n{context_str}"
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                options={"num_gpu": -1, "temperature": 0.2} # Low temperature for factual security reports
            )
            
            report = response['message']['content']
            return f"# Security Advisory: {cve_id}\n\n" + report
            
        except Exception as e:
            return f"Error during LLM Generation: {e}"

if __name__ == "__main__":
    analyzer = CVESecurityAnalyzer(model_name="gemma2:2b")
    report = analyzer.generate_sdl_report("CVE-2021-44228") # Log4j test
    print(report)
