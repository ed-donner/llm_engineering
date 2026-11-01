from pydantic import BaseModel


class InputMode(BaseModel):
    company_name:str
    url:str