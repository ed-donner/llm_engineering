"""
Agentic Code Review Assistant
=============================

An autonomous multi-agent system for intelligent code review and analysis.
This exercise demonstrates:
1. Multi-agent architecture with specialized agents
2. LLM-powered code analysis
3. Static analysis integration
4. Automated suggestion generation

Author: Emmanuel Ochade
Week 8 Community Contribution
"""

import os
import re
import ast
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(name)s] %(message)s")
logger = logging.getLogger("CodeReviewAgent")


class Severity(Enum):
    """Issue severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CodeIssue:
    """Represents a code issue found during review"""

    line_number: int
    severity: Severity
    category: str
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class ReviewResult:
    """Complete code review result"""

    file_name: str
    issues: List[CodeIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    score: float = 0.0


class BaseAgent(ABC):
    """Abstract base class for all review agents"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)

    @abstractmethod
    def analyze(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze code and return findings"""
        pass

    def log(self, message: str):
        self.logger.info(f"[{self.name}] {message}")


class SyntaxAnalyzerAgent(BaseAgent):
    """Agent for analyzing Python syntax and structure"""

    def __init__(self):
        super().__init__("SyntaxAnalyzer")

    def analyze(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log("Starting syntax analysis...")
        issues = []
        metrics = {
            "total_lines": len(code.split("\n")),
            "blank_lines": 0,
            "comment_lines": 0,
            "code_lines": 0,
            "functions": 0,
            "classes": 0,
            "imports": 0,
        }

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                metrics["blank_lines"] += 1
            elif stripped.startswith("#"):
                metrics["comment_lines"] += 1
            else:
                metrics["code_lines"] += 1

                # Check for common issues
                if len(line) > 120:
                    issues.append(
                        CodeIssue(
                            line_number=i,
                            severity=Severity.WARNING,
                            category="line_length",
                            message=f"Line exceeds 120 characters ({len(line)} chars)",
                            suggestion="Consider breaking this line into multiple lines",
                        )
                    )

                # Check for trailing whitespace
                if line.rstrip() != line:
                    issues.append(
                        CodeIssue(
                            line_number=i,
                            severity=Severity.INFO,
                            category="whitespace",
                            message="Trailing whitespace detected",
                            suggestion="Remove trailing whitespace",
                        )
                    )

        # Try to parse AST for deeper analysis
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics["functions"] += 1
                    # Check function complexity
                    if len(node.body) > 50:
                        issues.append(
                            CodeIssue(
                                line_number=node.lineno,
                                severity=Severity.WARNING,
                                category="complexity",
                                message=f"Function '{node.name}' is too long ({len(node.body)} statements)",
                                suggestion="Consider breaking into smaller functions",
                            )
                        )
                elif isinstance(node, ast.ClassDef):
                    metrics["classes"] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    metrics["imports"] += 1
        except SyntaxError as e:
            issues.append(
                CodeIssue(
                    line_number=e.lineno or 1,
                    severity=Severity.CRITICAL,
                    category="syntax_error",
                    message=f"Syntax error: {e.msg}",
                    suggestion="Fix the syntax error before continuing",
                )
            )

        self.log(f"Found {len(issues)} syntax issues")
        return {"issues": issues, "metrics": metrics}


class SecurityAnalyzerAgent(BaseAgent):
    """Agent for detecting security vulnerabilities"""

    DANGEROUS_PATTERNS = [
        (r"\beval\s*\(", "Use of eval() is dangerous - can execute arbitrary code"),
        (r"\bexec\s*\(", "Use of exec() is dangerous - can execute arbitrary code"),
        (r"\bos\.system\s*\(", "os.system() can be vulnerable to command injection"),
        (
            r"\bsubprocess\..*shell\s*=\s*True",
            "shell=True in subprocess is vulnerable to injection",
        ),
        (
            r"\bpickle\.loads?\s*\(",
            "pickle can execute arbitrary code during deserialization",
        ),
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected"),
        (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret detected"),
        (r"__import__\s*\(", "Dynamic import can be exploited"),
        (r"\.format\s*\([^)]*\%", "String formatting may be vulnerable to injection"),
    ]

    def __init__(self):
        super().__init__("SecurityAnalyzer")

    def analyze(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log("Scanning for security vulnerabilities...")
        issues = []

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, message in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        CodeIssue(
                            line_number=i,
                            severity=Severity.ERROR,
                            category="security",
                            message=message,
                            code_snippet=line.strip(),
                            suggestion="Review and remediate this security concern",
                        )
                    )

        self.log(f"Found {len(issues)} security issues")
        return {"issues": issues, "security_score": max(0, 100 - len(issues) * 15)}


class StyleAnalyzerAgent(BaseAgent):
    """Agent for checking code style and PEP8 compliance"""

    def __init__(self):
        super().__init__("StyleAnalyzer")

    def analyze(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log("Checking code style...")
        issues = []

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # Check indentation (should be 4 spaces)
            if line and not line.startswith(" " * 4) and line.startswith(" "):
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces % 4 != 0:
                    issues.append(
                        CodeIssue(
                            line_number=i,
                            severity=Severity.INFO,
                            category="style",
                            message=f"Indentation is {leading_spaces} spaces, should be multiple of 4",
                            suggestion="Use 4-space indentation",
                        )
                    )

            # Check for multiple statements on one line
            if ";" in line and not line.strip().startswith("#"):
                issues.append(
                    CodeIssue(
                        line_number=i,
                        severity=Severity.WARNING,
                        category="style",
                        message="Multiple statements on one line",
                        suggestion="Split into separate lines",
                    )
                )

            # Check for missing spaces around operators
            if re.search(r"[a-zA-Z0-9][=+\-*/][a-zA-Z0-9]", line):
                issues.append(
                    CodeIssue(
                        line_number=i,
                        severity=Severity.INFO,
                        category="style",
                        message="Missing spaces around operator",
                        suggestion="Add spaces around operators for readability",
                    )
                )

            # Check for proper naming conventions
            snake_case_violation = re.search(r"\bdef\s+([A-Z][a-zA-Z]*)\s*\(", line)
            if snake_case_violation:
                issues.append(
                    CodeIssue(
                        line_number=i,
                        severity=Severity.WARNING,
                        category="naming",
                        message=f"Function '{snake_case_violation.group(1)}' should use snake_case",
                        suggestion="Rename to use lowercase with underscores",
                    )
                )

        self.log(f"Found {len(issues)} style issues")
        return {"issues": issues, "style_score": max(0, 100 - len(issues) * 5)}


class DocumentationAnalyzerAgent(BaseAgent):
    """Agent for checking documentation quality"""

    def __init__(self):
        super().__init__("DocumentationAnalyzer")

    def analyze(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log("Analyzing documentation...")
        issues = []
        metrics = {
            "has_module_docstring": False,
            "functions_with_docstrings": 0,
            "functions_without_docstrings": 0,
            "classes_with_docstrings": 0,
            "classes_without_docstrings": 0,
        }

        try:
            tree = ast.parse(code)

            # Check for module docstring
            if ast.get_docstring(tree):
                metrics["has_module_docstring"] = True
            else:
                issues.append(
                    CodeIssue(
                        line_number=1,
                        severity=Severity.INFO,
                        category="documentation",
                        message="Missing module-level docstring",
                        suggestion="Add a docstring describing the module's purpose",
                    )
                )

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if ast.get_docstring(node):
                        metrics["functions_with_docstrings"] += 1
                    else:
                        metrics["functions_without_docstrings"] += 1
                        issues.append(
                            CodeIssue(
                                line_number=node.lineno,
                                severity=Severity.WARNING,
                                category="documentation",
                                message=f"Function '{node.name}' lacks a docstring",
                                suggestion="Add a docstring explaining what the function does",
                            )
                        )

                elif isinstance(node, ast.ClassDef):
                    if ast.get_docstring(node):
                        metrics["classes_with_docstrings"] += 1
                    else:
                        metrics["classes_without_docstrings"] += 1
                        issues.append(
                            CodeIssue(
                                line_number=node.lineno,
                                severity=Severity.WARNING,
                                category="documentation",
                                message=f"Class '{node.name}' lacks a docstring",
                                suggestion="Add a docstring describing the class",
                            )
                        )

        except SyntaxError:
            self.log("Could not parse code for documentation analysis")

        total_funcs = (
            metrics["functions_with_docstrings"]
            + metrics["functions_without_docstrings"]
        )
        doc_coverage = (
            (metrics["functions_with_docstrings"] / total_funcs * 100)
            if total_funcs > 0
            else 100
        )
        metrics["documentation_coverage"] = round(doc_coverage, 1)

        self.log(f"Documentation coverage: {doc_coverage:.1f}%")
        return {"issues": issues, "metrics": metrics}


class LLMReviewAgent(BaseAgent):
    """Agent that uses LLM for intelligent code review suggestions"""

    def __init__(self, api_key: str = None):
        super().__init__("LLMReviewer")
        self.api_key = (
            api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        )
        self.client = None

        if self.api_key:
            try:
                # Try Anthropic first
                if os.getenv("ANTHROPIC_API_KEY"):
                    from anthropic import Anthropic

                    self.client = Anthropic(api_key=self.api_key)
                    self.provider = "anthropic"
                else:
                    from openai import OpenAI

                    self.client = OpenAI(api_key=self.api_key)
                    self.provider = "openai"
            except ImportError:
                self.log(
                    "No LLM client available. Install anthropic or openai package."
                )

    def analyze(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        self.log("Generating AI-powered review...")

        if not self.client:
            return {
                "issues": [],
                "ai_summary": "LLM review unavailable - no API key configured",
                "suggestions": [],
            }

        prompt = f"""You are an expert code reviewer. Analyze the following Python code and provide:
1. A brief summary of what the code does
2. Top 3 specific, actionable improvements
3. Any potential bugs or edge cases

Code to review:
```python
{code[:3000]}  # Truncate for token limits
```

Respond in JSON format:
{{
    "summary": "brief description",
    "improvements": ["improvement 1", "improvement 2", "improvement 3"],
    "potential_bugs": ["bug 1", "bug 2"],
    "overall_quality": "good/moderate/needs_improvement"
}}"""

        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=500,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                result_text = response.content[0].text
            else:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=500,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                result_text = response.choices[0].message.content

            # Parse JSON response
            json_match = re.search(r"\{[\s\S]*\}", result_text)
            if json_match:
                result = json.loads(json_match.group())
                self.log("AI review completed successfully")
                return {
                    "issues": [],
                    "ai_summary": result.get("summary", ""),
                    "suggestions": result.get("improvements", []),
                    "potential_bugs": result.get("potential_bugs", []),
                    "quality_rating": result.get("overall_quality", "unknown"),
                }
        except Exception as e:
            self.log(f"Error during LLM review: {e}")

        return {
            "issues": [],
            "ai_summary": "Could not generate AI review",
            "suggestions": [],
        }


class CodeReviewOrchestrator:
    """Orchestrates multiple code review agents"""

    def __init__(self, enable_llm: bool = True):
        self.agents = [
            SyntaxAnalyzerAgent(),
            SecurityAnalyzerAgent(),
            StyleAnalyzerAgent(),
            DocumentationAnalyzerAgent(),
        ]

        if enable_llm:
            self.agents.append(LLMReviewAgent())

        self.logger = logging.getLogger("Orchestrator")

    def review(self, code: str, file_name: str = "untitled.py") -> ReviewResult:
        """Run all agents and aggregate results"""
        self.logger.info(f"Starting comprehensive review of {file_name}")

        result = ReviewResult(file_name=file_name)
        all_metrics = {}

        for agent in self.agents:
            try:
                agent_result = agent.analyze(code)

                # Collect issues
                if "issues" in agent_result:
                    result.issues.extend(agent_result["issues"])

                # Collect metrics
                if "metrics" in agent_result:
                    all_metrics.update(agent_result["metrics"])

                # Store other data
                for key, value in agent_result.items():
                    if key not in ["issues", "metrics"]:
                        all_metrics[key] = value

            except Exception as e:
                self.logger.error(f"Agent {agent.name} failed: {e}")

        result.metrics = all_metrics

        # Calculate overall score
        severity_weights = {
            Severity.INFO: 1,
            Severity.WARNING: 3,
            Severity.ERROR: 10,
            Severity.CRITICAL: 25,
        }

        penalty = sum(severity_weights[issue.severity] for issue in result.issues)
        result.score = max(0, min(100, 100 - penalty))

        # Generate summary
        issue_counts = {}
        for issue in result.issues:
            issue_counts[issue.severity.value] = (
                issue_counts.get(issue.severity.value, 0) + 1
            )

        result.summary = f"Review Score: {result.score}/100 | " + " | ".join(
            f"{k}: {v}" for k, v in issue_counts.items()
        )

        self.logger.info(f"Review complete: {result.summary}")
        return result


def format_review_report(result: ReviewResult) -> str:
    """Format review result as a readable report"""
    lines = [
        "=" * 60,
        f"CODE REVIEW REPORT: {result.file_name}",
        "=" * 60,
        "",
        f"Overall Score: {result.score}/100",
        f"Summary: {result.summary}",
        "",
        "-" * 40,
        "METRICS",
        "-" * 40,
    ]

    for key, value in result.metrics.items():
        if not key.startswith("ai_") and not isinstance(value, list):
            lines.append(f"  {key}: {value}")

    if result.metrics.get("ai_summary"):
        lines.extend(
            [
                "",
                "-" * 40,
                "AI ANALYSIS",
                "-" * 40,
                f"  {result.metrics['ai_summary']}",
            ]
        )

        if result.metrics.get("suggestions"):
            lines.append("\n  Suggestions:")
            for i, suggestion in enumerate(result.metrics["suggestions"], 1):
                lines.append(f"    {i}. {suggestion}")

    if result.issues:
        lines.extend(
            [
                "",
                "-" * 40,
                f"ISSUES FOUND ({len(result.issues)})",
                "-" * 40,
            ]
        )

        # Group by severity
        for severity in [
            Severity.CRITICAL,
            Severity.ERROR,
            Severity.WARNING,
            Severity.INFO,
        ]:
            severity_issues = [i for i in result.issues if i.severity == severity]
            if severity_issues:
                lines.append(f"\n  [{severity.value.upper()}]")
                for issue in severity_issues[:5]:  # Limit output
                    lines.append(f"    Line {issue.line_number}: {issue.message}")
                    if issue.suggestion:
                        lines.append(f"      -> {issue.suggestion}")
                if len(severity_issues) > 5:
                    lines.append(f"    ... and {len(severity_issues) - 5} more")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


# Example usage and demonstration
if __name__ == "__main__":
    # Sample code to review
    sample_code = '''
def calculate_price(items,tax_rate):
    """Calculate total price with tax"""
    total=0
    for item in items:
        total += item['price']
    total_with_tax = total * (1 + tax_rate)
    return total_with_tax

class shoppingCart:
    def __init__(self):
        self.items = []
        self.password = "secret123"  # Security issue!
    
    def AddItem(self, item):  # Naming convention issue
        self.items.append(item)
    
    def get_total(self):
        return calculate_price(self.items, 0.1)
    
    def process_data(self, data):
        result = eval(data)  # Security vulnerability!
        return result
'''

    print("Starting Agentic Code Review Assistant Demo")
    print("-" * 50)

    # Create orchestrator and run review
    orchestrator = CodeReviewOrchestrator(enable_llm=False)  # Disable LLM for demo
    result = orchestrator.review(sample_code, "sample_shopping_cart.py")

    # Print formatted report
    report = format_review_report(result)
    print(report)

    print("\nDemo complete! The agentic code review system analyzed:")
    print(f"  - {result.metrics.get('total_lines', 0)} lines of code")
    print(f"  - {result.metrics.get('functions', 0)} functions")
    print(f"  - {result.metrics.get('classes', 0)} classes")
    print(
        f"  - Found {len(result.issues)} issues across syntax, security, style, and documentation"
    )
