from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    REVIEW = "REVIEW"
    RISKY = "RISKY"


class SecurityIssue(BaseModel):
    type: str
    severity: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    description: str
    recommendation: str


class ComplianceViolation(BaseModel):
    rule: str
    severity: str
    file_path: Optional[str] = None
    description: str
    suggestion: str


class SecurityScore(BaseModel):
    risk: float
    issues: List[SecurityIssue] = []
    summary: str
    confidence: float = 0.8
    cost: float = 0.0


class ComplianceScore(BaseModel):
    risk: float
    violations: List[ComplianceViolation] = []
    passed_checks: List[str] = []
    summary: str


class RiskAssessment(BaseModel):
    overall_risk: float
    risk_level: RiskLevel
    security_score: SecurityScore
    compliance_score: ComplianceScore
    recommendation: str
    confidence: float = 0.8


class PullRequest(BaseModel):
    repo: str
    number: int
    title: str
    author: str
    url: str
    diff: str
    files_changed: List[str] = []
    created_at: datetime
    labels: List[str] = []


class ReviewResult(BaseModel):
    pr: PullRequest
    risk_assessment: RiskAssessment
    reviewed_at: datetime = Field(default_factory=datetime.now)

    def to_summary(self):
        risk = self.risk_assessment
        level_marker = "SAFE" if risk.risk_level == RiskLevel.SAFE else "REVIEW" if risk.risk_level == RiskLevel.REVIEW else "RISKY"

        summary = f"""PR #{self.pr.number}: {self.pr.title}
Overall Risk: {risk.overall_risk:.2f} - {level_marker}

Security: {risk.security_score.risk:.2f} - {risk.security_score.summary}
Compliance: {risk.compliance_score.risk:.2f} - {risk.compliance_score.summary}

Recommendation: {risk.recommendation}
"""
        return summary.strip()
