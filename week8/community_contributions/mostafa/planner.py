import ollama
import json
import re
from rag import retrieve_context, load_articles_to_chroma
from scanner import get_all_processes, get_new_or_changed_processes, load_fingerprints, save_fingerprints
from kb_updater import update_kb

class SecurityPlanner:
    def __init__(self, model="gemma3:4b"):
        self.model = model

    def analyse_process(self, proc_info):
        """Analyse a single process using RAG + LLM."""
        # Retrieve relevant articles
        query = f"Security issues related to {proc_info['name']} process on Linux"
        articles = retrieve_context(query, n_results=2)
        context = "\n".join(articles) if articles else "No specific articles found."

        # Build prompt
        prompt = f"""
You are a security analyst. Evaluate the following running process on a Linux system.

Process details:
- Name: {proc_info['name']}
- Executable: {proc_info['exe']}
- Command line: {proc_info['cmdline']}
- User: {proc_info['user']}
- Parent process: {proc_info['parent']}
- Network connections: {proc_info['connections']}
- Open files: {proc_info['open_files'][:5]} (showing first 5)

Relevant security knowledge from our database:
{context}

Based on this information, determine if the process is suspicious or vulnerable.
Answer in JSON format with fields:
- "is_suspicious": true/false
- "risk_level": "High"/"Medium"/"Low"/"None"
- "reasoning": string explaining your assessment
- "mitigation": actionable steps to reduce risk
"""

        response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']

        # Extract JSON
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(content)
        except:
            result = {
                "is_suspicious": "suspicious" in content.lower(),
                "risk_level": "Unknown",
                "reasoning": content[:500],
                "mitigation": "See above"
            }
        return result

    def run(self, update_kb=False):
        """Run the full scan and report."""
        # Optionally update knowledge base
        if update_kb:
            print("Updating knowledge base...")
            updated = update_kb()
            if updated:
                print(f"Knowledge base updated. {updated} articles added.")
                load_articles_to_chroma(rebuild=True)
            else:
                print("Knowledge base is up to date.")

        # Get all processes
        all_procs = get_all_processes()
        print(f"Found {len(all_procs)} processes.")

        # Load previous fingerprints
        fingerprints = load_fingerprints()

        # Get only new/changed processes (simplified: compare by exe+cmdline+user)
        new_procs = []
        for p in all_procs:
            key = f"{p['exe']}|{p['cmdline']}|{p['user']}"
            if key not in fingerprints:
                new_procs.append(p)

        print(f"New/changed processes to analyse: {len(new_procs)}")

        results = []
        for proc in new_procs:
            print(f"Analysing {proc['name']} (PID {proc['pid']})...")
            analysis = self.analyse_process(proc)
            results.append({
                "process": proc,
                "analysis": analysis
            })
            # Update fingerprint (store last_analyzed timestamp)
            key = f"{proc['exe']}|{proc['cmdline']}|{proc['user']}"
            fingerprints[key] = {
                "last_analyzed": str(proc.get('timestamp', '')),
                "last_result": analysis
            }

        save_fingerprints(fingerprints)
        return results