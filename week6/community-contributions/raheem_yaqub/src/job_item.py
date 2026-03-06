from pydantic import BaseModel


class JobItem(BaseModel):

    title: str
    company: str
    location: str
    experience: str
    skills: str
    salary: float
    description: str

    prompt: str | None = None

    def make_prompt(self):

        self.prompt = f"""
Estimate the salary for the following job.

Job Title: {self.title}
Company: {self.company}
Location: {self.location}
Experience: {self.experience}
Skills: {self.skills}

Salary is ${round(self.salary)}
"""

    def test_prompt(self):

        return self.prompt.split("Salary is")[0] + "Salary is $"