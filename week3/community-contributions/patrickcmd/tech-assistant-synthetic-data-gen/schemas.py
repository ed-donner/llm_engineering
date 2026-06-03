from pydantic import BaseModel


class DataPoint(BaseModel):
    system_prompt: str
    prompt: str
    completion: str


class SyntheticDataset(BaseModel):
    data: list[DataPoint]