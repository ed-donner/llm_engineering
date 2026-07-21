from pydantic import BaseModel
from pydantic import Field
from typing import Literal

TaskType = Literal["research_summary", "email_review", "meeting_actions", "risk_review", "rewrite"]

class PromptExperiment(BaseModel):
    name: str = Field(description="The name of the experiment", min_length=3)
    task_type: TaskType = Field(description="The task for the experiment", min_length=5)
    system_prompt: str = Field(description="The system prompt for the experiment", min_length=10)
    user_input: str = Field(description="The user input for the experiment", min_length=1)

class ExperimentResult(BaseModel):
    experiment_name: str 
    task_type: TaskType
    response: str | None = None
    success: bool
    error: str | None = None