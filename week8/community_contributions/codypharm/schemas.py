from pydantic import BaseModel, Field
from typing import List, Optional

# --- Input Models ---

class Drug(BaseModel):
    name: str = Field(..., description="Name of the drug (e.g. Amoxicillin)")
    dosage: str = Field(..., description="Dosage strength (e.g. 500mg)")
    frequency: str = Field(..., description="Frequency (e.g. 3x daily)")

class PatientProfile(BaseModel):
    age: int
    weight_kg: float
    allergies: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)

class PrescriptionInput(BaseModel):
    patient: PatientProfile
    drugs: List[Drug]

# --- Output Models (The Council's Verdict) ---

class Finding(BaseModel):
    severity: str = Field(..., description="SAFE, WARNING, or CRITICAL")
    message: str = Field(..., description="Explanation of the finding")

class AgentReport(BaseModel):
    agent_name: str
    status: str = Field(..., description="GREEN (Safe), YELLOW (Warning), RED (Danger)")
    findings: List[Finding]


class FinalVerdict(BaseModel):
    status: str = Field(..., description="GREEN (Dispense), YELLOW (Caution), RED (Do Not Dispense)")
    summary: str = Field(..., description="Executive summary for the pharmacist.")
    required_actions: List[str] = Field(..., description="Specific steps to resolve issues (e.g. 'Call Prescriber')")