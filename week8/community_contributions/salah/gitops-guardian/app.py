import os
import json
from pathlib import Path
from datetime import datetime
from typing import List
from dotenv import load_dotenv

import gradio as gr

from models import PullRequest, ReviewResult, RiskLevel, SecurityIssue, ComplianceViolation, SecurityScore, ComplianceScore, RiskAssessment
from agents import GitOpsScannerAgent, SecurityAgent, ComplianceAgent, RiskEnsembleAgent


class GitOpsGuardian:
    MEMORY_FILE = "reviewed_prs.json"

    def __init__(self):
        load_dotenv()

        self.github_token = os.getenv('GITHUB_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gitops_repos = os.getenv('GITOPS_REPOS', '').split(',')

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN not found")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found")
        if not self.gitops_repos or self.gitops_repos == ['']:
            raise ValueError("GITOPS_REPOS not found")

        self.scanner = GitOpsScannerAgent(self.github_token)
        self.security_agent = SecurityAgent(self.openai_api_key)
        self.compliance_agent = ComplianceAgent(self.github_token)
        self.ensemble_agent = RiskEnsembleAgent()

        self.total_cost = 0.0
        self.history_file = "review_history.json"
        self.memory = self._load_memory()

    def _load_memory(self):
        if Path(self.MEMORY_FILE).exists():
            try:
                with open(self.MEMORY_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('reviewed_prs', [])
            except:
                return []
        return []

    def _save_memory(self):
        try:
            data = {
                'reviewed_prs': self.memory,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.MEMORY_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def scan_prs(self):
        prs = self.scanner.scan(self.gitops_repos, self.memory)
        return prs

    def review_pr(self, pr):
        security_score = self.security_agent.review(pr)
        compliance_score = self.compliance_agent.review(pr)
        risk_assessment = self.ensemble_agent.assess(security_score, compliance_score)

        result = ReviewResult(
            pr=pr,
            risk_assessment=risk_assessment,
            reviewed_at=datetime.now()
        )

        if pr.url not in self.memory:
            self.memory.append(pr.url)
            self._save_memory()

        self.total_cost += security_score.cost
        self._save_history(result)

        return result

    def _save_history(self, result):
        try:
            history = []
            if Path(self.history_file).exists():
                with open(self.history_file, 'r') as f:
                    history = json.load(f)

            history.append({
                'pr_number': result.pr.number,
                'pr_url': result.pr.url,
                'repo': result.pr.repo,
                'title': result.pr.title,
                'author': result.pr.author,
                'risk_score': result.risk_assessment.overall_risk,
                'risk_level': result.risk_assessment.risk_level.value,
                'security_risk': result.risk_assessment.security_score.risk,
                'security_summary': result.risk_assessment.security_score.summary,
                'compliance_risk': result.risk_assessment.compliance_score.risk,
                'compliance_summary': result.risk_assessment.compliance_score.summary,
                'security_issues_count': len(result.risk_assessment.security_score.issues),
                'compliance_violations_count': len(result.risk_assessment.compliance_score.violations),
                'cost': result.risk_assessment.security_score.cost,
                'reviewed_at': result.reviewed_at.isoformat()
            })

            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except:
            pass

    def post_pr_comment(self, pr, result):
        try:
            from github import Github
            gh = Github(self.github_token)
            repo = gh.get_repo(pr.repo)
            pr_obj = repo.get_pull(pr.number)

            comment = f"""## GitOps Guardian Security Review

**Risk Level:** {result.risk_assessment.risk_level.value} (Score: {result.risk_assessment.overall_risk:.2f})

### Security Analysis
- **Risk:** {result.risk_assessment.security_score.risk:.2f}
- **Issues Found:** {len(result.risk_assessment.security_score.issues)}
- **Summary:** {result.risk_assessment.security_score.summary}

### Compliance Check
- **Risk:** {result.risk_assessment.compliance_score.risk:.2f}
- **Violations:** {len(result.risk_assessment.compliance_score.violations)}
- **Summary:** {result.risk_assessment.compliance_score.summary}

### Recommendation
{result.risk_assessment.recommendation}

---
*Automated review by GitOps Guardian*
"""
            pr_obj.create_issue_comment(comment)
            return True
        except:
            return False

    def review_all(self):
        prs = self.scan_prs()

        if not prs:
            return []

        results = []
        for pr in prs:
            try:
                result = self.review_pr(pr)
                results.append(result)
            except:
                pass

        return results


def create_gradio_app():
    try:
        app = GitOpsGuardian()
    except Exception as e:
        raise

    def load_historical_results():
        historical_results = []
        try:
            if Path(app.history_file).exists():
                with open(app.history_file, 'r') as f:
                    history = json.load(f)

                    for entry in history:
                        issues_count = entry.get('security_issues_count', 0)
                        violations_count = entry.get('compliance_violations_count', 0)

                        pr = PullRequest(
                            repo=entry['repo'],
                            number=entry['pr_number'],
                            title=entry.get('title', f"PR #{entry['pr_number']}"),
                            author=entry.get('author', 'unknown'),
                            url=entry['pr_url'],
                            diff="",
                            files_changed=[],
                            created_at=datetime.fromisoformat(entry['reviewed_at']),
                            labels=[]
                        )

                        security_issues = [
                            SecurityIssue(
                                type="historical",
                                severity="info",
                                description=f"Historical record ({issues_count} issues found)",
                                recommendation=""
                            )
                        ] if issues_count > 0 else []

                        compliance_violations = [
                            ComplianceViolation(
                                rule="historical",
                                severity="info",
                                description=f"Historical record ({violations_count} violations found)",
                                recommendation=""
                            )
                        ] if violations_count > 0 else []

                        security_score = SecurityScore(
                            risk=entry['security_risk'],
                            issues=security_issues,
                            summary=entry.get('security_summary', 'Historical review'),
                            cost=entry.get('cost', 0.0)
                        )

                        compliance_score = ComplianceScore(
                            risk=entry['compliance_risk'],
                            violations=compliance_violations,
                            passed_checks=[],
                            summary=entry.get('compliance_summary', 'Historical review')
                        )

                        risk_assessment = RiskAssessment(
                            overall_risk=entry['risk_score'],
                            risk_level=RiskLevel(entry['risk_level']),
                            security_score=security_score,
                            compliance_score=compliance_score,
                            recommendation="",
                            confidence=0.85
                        )

                        result = ReviewResult(
                            pr=pr,
                            risk_assessment=risk_assessment,
                            reviewed_at=datetime.fromisoformat(entry['reviewed_at'])
                        )

                        historical_results.append(result)
        except:
            pass

        return historical_results

    all_results = load_historical_results()
    post_comments_enabled = [False]

    def export_json():
        if not all_results:
            return None
        try:
            export_data = [
                {
                    'pr_number': r.pr.number,
                    'title': r.pr.title,
                    'repo': r.pr.repo,
                    'url': r.pr.url,
                    'risk_score': r.risk_assessment.overall_risk,
                    'risk_level': r.risk_assessment.risk_level.value,
                    'security_risk': r.risk_assessment.security_score.risk,
                    'compliance_risk': r.risk_assessment.compliance_score.risk,
                    'reviewed_at': r.reviewed_at.isoformat()
                } for r in all_results
            ]
            path = "gitops_guardian_export.json"
            with open(path, 'w') as f:
                json.dump(export_data, f, indent=2)
            return path
        except:
            return None

    def export_csv():
        if not all_results:
            return None
        try:
            import csv
            path = "gitops_guardian_export.csv"
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['PR', 'Title', 'Repo', 'Risk Score', 'Level', 'Security', 'Compliance', 'URL'])
                for r in all_results:
                    writer.writerow([
                        r.pr.number, r.pr.title, r.pr.repo,
                        f"{r.risk_assessment.overall_risk:.2f}",
                        r.risk_assessment.risk_level.value,
                        f"{r.risk_assessment.security_score.risk:.2f}",
                        f"{r.risk_assessment.compliance_score.risk:.2f}",
                        r.pr.url
                    ])
            return path
        except:
            return None

    def scan_and_review():
        try:
            results = app.review_all()

            if not results:
                if all_results:
                    table_data = format_table(all_results)
                    summary = "No new PRs found. Showing historical reviews below."
                    stats = format_stats(all_results)
                    return table_data, summary, stats
                else:
                    return format_table([]), "No new PRs found", ""

            if post_comments_enabled[0]:
                for result in results:
                    app.post_pr_comment(result.pr, result)

            all_results.extend(results)

            table_data = format_table(all_results)
            summary = format_summary(results)
            stats = format_stats(all_results)

            return table_data, summary, stats

        except Exception as e:
            error_msg = f"Error during scan: {str(e)}"
            return [], error_msg, ""

    def format_table(results):
        table_data = []

        for result in results:
            pr = result.pr
            risk = result.risk_assessment

            if risk.risk_level == RiskLevel.SAFE:
                emoji = "SAFE"
            elif risk.risk_level == RiskLevel.REVIEW:
                emoji = "REVIEW"
            else:
                emoji = "RISKY"

            row = [
                f"{emoji} #{pr.number}",
                pr.title,
                pr.repo,
                f"{risk.overall_risk:.2f}",
                risk.risk_level.value,
                f"{risk.security_score.risk:.2f}",
                f"{risk.compliance_score.risk:.2f}",
                len(risk.security_score.issues),
                len(risk.compliance_score.violations),
                pr.url
            ]
            table_data.append(row)

        return table_data

    def format_summary(results):
        if not results:
            return "No results"

        summary = f"## Latest Scan Results\n\n"
        summary += f"**Scanned**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += f"**PRs Reviewed**: {len(results)}\n\n"

        for result in results:
            pr = result.pr
            risk = result.risk_assessment

            level_marker = "SAFE" if risk.risk_level == RiskLevel.SAFE else "REVIEW" if risk.risk_level == RiskLevel.REVIEW else "RISKY"

            summary += f"### PR #{pr.number}: {pr.title}\n\n"
            summary += f"**Risk**: {risk.overall_risk:.2f} ({level_marker})\n\n"
            summary += f"**Security**: {risk.security_score.risk:.2f} - {risk.security_score.summary}\n\n"

            if risk.security_score.issues:
                summary += "**Security Issues**:\n"
                for issue in risk.security_score.issues[:3]:
                    summary += f"- [{issue.severity}] {issue.description}\n"
                summary += "\n"

            summary += f"**Compliance**: {risk.compliance_score.risk:.2f} - {risk.compliance_score.summary}\n\n"

            if risk.compliance_score.violations:
                summary += "**Compliance Violations**:\n"
                for violation in risk.compliance_score.violations[:3]:
                    summary += f"- [{violation.severity}] {violation.description}\n"
                summary += "\n"

            summary += f"**Recommendation**: {risk.recommendation}\n\n"
            summary += "---\n\n"

        return summary

    def format_stats(results):
        if not results:
            return "No statistics available"

        total = len(results)
        safe = sum(1 for r in results if r.risk_assessment.risk_level == RiskLevel.SAFE)
        review = sum(1 for r in results if r.risk_assessment.risk_level == RiskLevel.REVIEW)
        risky = sum(1 for r in results if r.risk_assessment.risk_level == RiskLevel.RISKY)

        avg_risk = sum(r.risk_assessment.overall_risk for r in results) / total

        history_stats = ""
        try:
            if Path(app.history_file).exists():
                with open(app.history_file, 'r') as f:
                    history = json.load(f)
                    if len(history) > 1:
                        recent_risks = [h['risk_score'] for h in history[-10:]]
                        trend = "Increasing" if recent_risks[-1] > recent_risks[0] else "Decreasing"
                        history_stats = f"\n**Historical Trend** (last 10): {trend}\n**Total Reviews**: {len(history)}"
        except:
            pass

        stats = f"""## Overall Statistics

**Total PRs Reviewed**: {total}

**Risk Distribution**:
- Safe: {safe} ({safe/total*100:.1f}%)
- Review: {review} ({review/total*100:.1f}%)
- Risky: {risky} ({risky/total*100:.1f}%)

**Average Risk Score**: {avg_risk:.2f}

**Session Cost**: ${app.total_cost:.6f}
{history_stats}

**Repositories**: {', '.join(app.gitops_repos)}
"""
        return stats

    with gr.Blocks(title="GitOps Guardian", theme=gr.themes.Soft()) as interface:

        gr.Markdown("""
# GitOps Guardian

**AI-Powered Pull Request Security & Compliance Review**

Multi-agent system that scans GitOps repositories and identifies security risks and compliance violations.
        """)

        with gr.Row():
            scan_button = gr.Button("Scan Repositories & Review PRs", variant="primary", size="lg")
            post_comment_checkbox = gr.Checkbox(label="Post results as PR comments", value=False)

        with gr.Row():
            export_json_btn = gr.Button("Export JSON", size="sm")
            export_csv_btn = gr.Button("Export CSV", size="sm")
            json_file = gr.File(label="Download JSON", visible=False)
            csv_file = gr.File(label="Download CSV", visible=False)

        gr.Markdown("## Review Results")

        initial_table = format_table(all_results) if all_results else []
        initial_summary = "Historical reviews loaded. Click 'Scan' to check for new PRs." if all_results else "Click 'Scan' to review PRs"
        initial_stats = format_stats(all_results) if all_results else "No reviews yet"

        with gr.Row():
            pr_table = gr.Dataframe(
                headers=[
                    "PR #", "Title", "Repo", "Risk Score", "Level",
                    "Security", "Compliance", "Security Issues",
                    "Violations", "URL"
                ],
                value=initial_table,
                label="Pull Requests",
                wrap=True,
                interactive=False,
                column_widths=["5%", "20%", "15%", "8%", "8%", "8%", "8%", "8%", "8%", "12%"]
            )

        with gr.Row():
            with gr.Column(scale=2):
                summary_output = gr.Markdown(value=initial_summary, label="Detailed Results")
            with gr.Column(scale=1):
                stats_output = gr.Markdown(value=initial_stats, label="Statistics")

        gr.Markdown("""
## How It Works

1. **Scanner Agent** - Fetches open PRs from configured GitOps repos
2. **Security Agent** - Analyzes for secrets and vulnerabilities using OpenAI
3. **Compliance Agent** - Validates Kubernetes best practices
4. **Ensemble Agent** - Combines scores into risk assessment

## Configuration

Set these in `.env`:
- `GITHUB_TOKEN` - GitHub personal access token
- `OPENAI_API_KEY` - OpenAI API key
- `GITOPS_REPOS` - Comma-separated repo names (owner/repo)
        """)

        def update_comment_setting(enabled):
            post_comments_enabled[0] = enabled
            return f"PR comments: {'Enabled' if enabled else 'Disabled'}"

        post_comment_checkbox.change(
            fn=update_comment_setting,
            inputs=[post_comment_checkbox],
            outputs=[]
        )

        scan_button.click(
            fn=scan_and_review,
            inputs=[],
            outputs=[pr_table, summary_output, stats_output]
        )

        export_json_btn.click(
            fn=export_json,
            inputs=[],
            outputs=[json_file]
        )

        export_csv_btn.click(
            fn=export_csv,
            inputs=[],
            outputs=[csv_file]
        )

    return interface


def main():
    print("\nGitOps Guardian - AI-Powered PR Review System\n")

    try:
        interface = create_gradio_app()
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )
    except Exception as e:
        print(f"Failed to start: {e}")
        raise


if __name__ == "__main__":
    main()
