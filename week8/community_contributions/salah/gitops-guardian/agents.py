import os
import re
import yaml
from typing import List, Dict
from openai import OpenAI
from github import Github

from models import (
    PullRequest, SecurityScore, ComplianceScore, RiskAssessment,
    SecurityIssue, ComplianceViolation, RiskLevel
)


class Agent:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BG_BLACK = '\033[40m'
    RESET = '\033[0m'

    name = "Agent"
    color = WHITE

    def log(self, message):
        pass


class GitOpsScannerAgent(Agent):
    name = "GitOps Scanner"
    color = Agent.CYAN

    def __init__(self, github_token):
        self.github = Github(github_token)

    def scan(self, repos, memory=[]):
        all_prs = []

        for repo_name in repos:
            try:
                repo = self.github.get_repo(repo_name)
                pulls = repo.get_pulls(state='open', sort='created', direction='desc')

                for pr in pulls:
                    pr_url = pr.html_url

                    if pr_url in memory:
                        continue

                    files = pr.get_files()
                    diff_content = ""
                    files_changed = []

                    for file in files:
                        files_changed.append(file.filename)
                        if file.patch:
                            diff_content += f"\n\n--- {file.filename}\n{file.patch}"

                    pull_request = PullRequest(
                        repo=repo_name,
                        number=pr.number,
                        title=pr.title,
                        author=pr.user.login,
                        url=pr_url,
                        diff=diff_content,
                        files_changed=files_changed,
                        created_at=pr.created_at,
                        labels=[label.name for label in pr.labels]
                    )

                    all_prs.append(pull_request)

            except Exception as e:
                pass

        return all_prs


class SecurityAgent(Agent):
    name = "Security Agent"
    color = Agent.RED

    def __init__(self, openai_api_key):
        self.client = OpenAI(api_key=openai_api_key)

    def review(self, pr):
        system_prompt = """You are a security expert analyzing GitOps infrastructure changes.
Identify security issues in Kubernetes manifests, Helm charts, and infrastructure code.

Focus on:
1. Hardcoded secrets (AWS keys, passwords, tokens, API keys)
2. Insecure container configurations (privileged mode, hostNetwork)
3. Missing security contexts
4. Overly permissive RBAC
5. Exposed services without proper restrictions
6. Using :latest tags or insecure images

Respond in JSON format:
{
    "risk_score": 0.0-1.0,
    "issues": [
        {
            "type": "hardcoded_secret",
            "severity": "critical|high|medium|low",
            "description": "Found AWS access key",
            "line_number": 15,
            "file_path": "deployment.yaml",
            "recommendation": "Use Kubernetes Secret instead"
        }
    ],
    "summary": "Brief summary of findings"
}
"""

        user_prompt = f"""Analyze this GitOps pull request for security issues:

Title: {pr.title}
Files changed: {', '.join(pr.files_changed)}

Diff:
{pr.diff[:3000]}

Identify any security concerns."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)

            result = eval(response.choices[0].message.content)

            issues = []
            for issue_dict in result.get('issues', []):
                issue = SecurityIssue(
                    type=issue_dict.get('type', 'unknown'),
                    severity=issue_dict.get('severity', 'medium'),
                    line_number=issue_dict.get('line_number'),
                    file_path=issue_dict.get('file_path'),
                    description=issue_dict.get('description', ''),
                    recommendation=issue_dict.get('recommendation', '')
                )
                issues.append(issue)

            risk_score = float(result.get('risk_score', 0.0))
            summary = result.get('summary', 'No issues found')

            return SecurityScore(
                risk=risk_score,
                issues=issues,
                summary=summary,
                confidence=0.85,
                cost=cost
            )

        except Exception as e:
            return SecurityScore(
                risk=0.5,
                issues=[],
                summary=f"Error during analysis: {str(e)}",
                confidence=0.3
            )


class ComplianceAgent(Agent):
    name = "Compliance Agent"
    color = Agent.YELLOW

    def __init__(self, github_token=None):
        self.github_client = Github(github_token) if github_token else None

    def review(self, pr):
        violations = []
        passed_checks = []

        yaml_files = self._extract_yaml_files(pr.diff, pr.files_changed)

        for file_path, content in yaml_files.items():
            try:
                docs = list(yaml.safe_load_all(content))

                for doc in docs:
                    if not doc or not isinstance(doc, dict):
                        continue

                    image_violations = self._check_image_tags(doc, file_path)
                    violations.extend(image_violations)
                    if not image_violations:
                        passed_checks.append(f"Image tags OK in {file_path}")

                    limit_violations = self._check_resource_limits(doc, file_path)
                    violations.extend(limit_violations)
                    if not limit_violations:
                        passed_checks.append(f"Resource limits OK in {file_path}")

                    label_violations = self._check_labels(doc, file_path)
                    violations.extend(label_violations)
                    if not label_violations:
                        passed_checks.append(f"Labels OK in {file_path}")

                    security_violations = self._check_security_context(doc, file_path)
                    violations.extend(security_violations)
                    if not security_violations:
                        passed_checks.append(f"Security context OK in {file_path}")

            except Exception as e:
                pass

        risk_score = min(1.0, len(violations) / 10.0)
        summary = f"Found {len(violations)} violations, {len(passed_checks)} checks passed"

        return ComplianceScore(
            risk=risk_score,
            violations=violations,
            passed_checks=passed_checks,
            summary=summary
        )

    def _extract_yaml_files(self, diff, files_changed):
        yaml_files = {}

        for file_path in files_changed:
            if file_path.endswith(('.yaml', '.yml')):
                lines = []
                in_file = False

                for line in diff.split('\n'):
                    if f"--- {file_path}" in line or f"+++ {file_path}" in line:
                        in_file = True
                        continue
                    if line.startswith('---') or line.startswith('+++'):
                        in_file = False
                    if in_file:
                        if not line.startswith('-') and not line.startswith('@@'):
                            clean_line = line[1:] if line.startswith('+') else line
                            lines.append(clean_line)

                if lines:
                    yaml_files[file_path] = '\n'.join(lines)

        return yaml_files

    def _check_image_tags(self, doc, file_path):
        violations = []
        containers = self._get_containers(doc)

        for container in containers:
            image = container.get('image', '')

            if ':latest' in image:
                violations.append(ComplianceViolation(
                    rule="no_latest_tags",
                    severity="error",
                    file_path=file_path,
                    description=f"Container using :latest tag: {image}",
                    suggestion="Use semantic versioning (e.g., v1.2.3) or image digest"
                ))
            elif ':' not in image:
                violations.append(ComplianceViolation(
                    rule="explicit_tag_required",
                    severity="warning",
                    file_path=file_path,
                    description=f"Container missing explicit tag: {image}",
                    suggestion="Add explicit version tag"
                ))

        return violations

    def _check_resource_limits(self, doc, file_path):
        violations = []
        containers = self._get_containers(doc)

        for container in containers:
            resources = container.get('resources', {})
            limits = resources.get('limits', {})

            if not limits.get('cpu'):
                violations.append(ComplianceViolation(
                    rule="cpu_limits_required",
                    severity="warning",
                    file_path=file_path,
                    description=f"Container '{container.get('name')}' missing CPU limits",
                    suggestion="Add resources.limits.cpu"
                ))

            if not limits.get('memory'):
                violations.append(ComplianceViolation(
                    rule="memory_limits_required",
                    severity="warning",
                    file_path=file_path,
                    description=f"Container '{container.get('name')}' missing memory limits",
                    suggestion="Add resources.limits.memory"
                ))

        return violations

    def _check_labels(self, doc, file_path):
        violations = []
        metadata = doc.get('metadata', {})
        labels = metadata.get('labels', {})

        required_labels = ['app', 'version']

        for label in required_labels:
            if label not in labels:
                violations.append(ComplianceViolation(
                    rule="required_labels",
                    severity="warning",
                    file_path=file_path,
                    description=f"Missing required label: {label}",
                    suggestion=f"Add metadata.labels.{label}"
                ))

        return violations

    def _check_security_context(self, doc, file_path):
        violations = []
        containers = self._get_containers(doc)

        for container in containers:
            security_context = container.get('securityContext', {})

            if security_context.get('privileged'):
                violations.append(ComplianceViolation(
                    rule="no_privileged_containers",
                    severity="error",
                    file_path=file_path,
                    description=f"Container '{container.get('name')}' running in privileged mode",
                    suggestion="Remove privileged: true unless absolutely necessary"
                ))

        if doc.get('kind') == 'Pod':
            spec = doc.get('spec', {})
            if spec.get('hostNetwork'):
                violations.append(ComplianceViolation(
                    rule="no_host_network",
                    severity="error",
                    file_path=file_path,
                    description="Pod using host network",
                    suggestion="Remove hostNetwork: true unless required"
                ))

        return violations

    def _get_containers(self, doc):
        containers = []

        if doc.get('kind') in ['Deployment', 'StatefulSet', 'DaemonSet', 'Job', 'CronJob']:
            spec = doc.get('spec', {})
            template = spec.get('template', {})
            pod_spec = template.get('spec', {})
            containers = pod_spec.get('containers', [])
        elif doc.get('kind') == 'Pod':
            spec = doc.get('spec', {})
            containers = spec.get('containers', [])

        return containers


class RiskEnsembleAgent(Agent):
    name = "Risk Ensemble"
    color = Agent.GREEN

    SECURITY_WEIGHT = 0.6
    COMPLIANCE_WEIGHT = 0.4

    def __init__(self):
        pass

    def assess(self, security_score, compliance_score):
        overall_risk = (
            security_score.risk * self.SECURITY_WEIGHT +
            compliance_score.risk * self.COMPLIANCE_WEIGHT
        )

        if overall_risk < 0.3:
            risk_level = RiskLevel.SAFE
            recommendation = "SAFE TO MERGE - No significant issues found"
        elif overall_risk < 0.7:
            risk_level = RiskLevel.REVIEW
            recommendation = "REVIEW NEEDED - Address issues before merging"
        else:
            risk_level = RiskLevel.RISKY
            recommendation = "HIGH RISK - Do not merge until critical issues are resolved"

        confidence = (security_score.confidence + 0.9) / 2

        return RiskAssessment(
            overall_risk=overall_risk,
            risk_level=risk_level,
            security_score=security_score,
            compliance_score=compliance_score,
            recommendation=recommendation,
            confidence=confidence
        )
