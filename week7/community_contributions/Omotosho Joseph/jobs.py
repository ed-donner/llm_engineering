from pydantic import BaseModel
from datasets import Dataset, DatasetDict, load_dataset
from typing import Optional, Self


PREFIX = "Salary is $"
QUESTION = "What is the annual salary for this position to the nearest thousand dollars?"

MIN_CHARS = 100
MIN_SALARY = 15_000
MAX_SALARY = 500_000
MAX_TEXT = 3000


class Job(BaseModel):
    title: str
    category: str
    salary: float
    full: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[str] = None
    schedule_type: Optional[str] = None
    work_from_home: Optional[bool] = None
    summary: Optional[str] = None
    prompt: Optional[str] = None
    completion: Optional[str] = None
    id: Optional[int] = None

    def make_prompt(self, text: str):
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}{round(self.salary / 1000) * 1000:.0f}"

    def test_prompt(self) -> str:
        return self.prompt.split(PREFIX)[0] + PREFIX

    def __repr__(self) -> str:
        return f"<{self.title} = ${self.salary:,.0f}>"

    def count_tokens(self, tokenizer):
        return len(tokenizer.encode(self.summary or self.full or "", add_special_tokens=False))

    def make_prompts(self, tokenizer, max_tokens, do_round):
        """Build prompt + completion for SFT training.
        do_round=True rounds salary to nearest $1000 (for train/val).
        do_round=False keeps the raw salary (for test).
        """
        text = self.summary or self.full or ""
        tokens = tokenizer.encode(text, add_special_tokens=False)
        if len(tokens) > max_tokens:
            text = tokenizer.decode(tokens[:max_tokens]).rstrip()
        self.prompt = f"{QUESTION}\n\n{text}\n\n{PREFIX}"
        if do_round:
            self.completion = f"{round(self.salary / 1000) * 1000:.0f}"
        else:
            self.completion = f"{self.salary:.0f}"

    def count_prompt_tokens(self, tokenizer):
        full = self.prompt + self.completion
        return len(tokenizer.encode(full, add_special_tokens=False))

    def to_datapoint(self) -> dict:
        return {"prompt": self.prompt, "completion": self.completion}

    @staticmethod
    def push_to_hub(dataset_name: str, train: list[Self], val: list[Self], test: list[Self]):
        DatasetDict(
            {
                "train": Dataset.from_list([job.model_dump() for job in train]),
                "validation": Dataset.from_list([job.model_dump() for job in val]),
                "test": Dataset.from_list([job.model_dump() for job in test]),
            }
        ).push_to_hub(dataset_name)

    @staticmethod
    def push_prompts_to_hub(dataset_name: str, train: list[Self], val: list[Self], test: list[Self]):
        DatasetDict(
            {
                "train": Dataset.from_list([job.to_datapoint() for job in train]),
                "val": Dataset.from_list([job.to_datapoint() for job in val]),
                "test": Dataset.from_list([job.to_datapoint() for job in test]),
            }
        ).push_to_hub(dataset_name)

    @classmethod
    def from_hub(cls, dataset_name: str) -> tuple[list[Self], list[Self], list[Self]]:
        ds = load_dataset(dataset_name)
        return (
            [cls.model_validate(row) for row in ds["train"]],
            [cls.model_validate(row) for row in ds["validation"]],
            [cls.model_validate(row) for row in ds["test"]],
        )


def simplify(text) -> str:
    if text is None:
        return ""
    return (
        str(text)
        .replace("\n", " ")
        .replace("\r", "")
        .replace("\t", " ")
        .replace("  ", " ")
        .strip()[:MAX_TEXT]
    )


def scrub(title, company, location, description, skills, schedule_type) -> str:
    result = f"Job Title: {title}\n"
    if company:
        result += f"Company: {simplify(company)}\n"
    if location:
        result += f"Location: {simplify(location)}\n"
    if schedule_type:
        result += f"Type: {simplify(schedule_type)}\n"
    if skills:
        result += f"Skills: {simplify(skills)}\n"
    if description:
        result += f"Description: {simplify(description)}\n"
    return result.strip()[:MAX_TEXT]


def parse(row):
    try:
        salary = row.get("salary_year_avg")
        if salary is None or salary != salary:
            return None
        salary = float(salary)
    except (ValueError, TypeError):
        return None

    if not (MIN_SALARY <= salary <= MAX_SALARY):
        return None

    title = row.get("job_title") or row.get("job_title_short") or ""
    if not title:
        return None

    company = row.get("company_name") or ""
    location = row.get("job_location") or ""
    category = row.get("job_title_short") or "Other"
    skills = row.get("job_skills") or ""
    schedule_type = row.get("job_schedule_type") or ""
    work_from_home = bool(row.get("job_work_from_home", False))

    full = scrub(title, company, location, "", skills, schedule_type)
    if len(full) < MIN_CHARS:
        return None

    return Job(
        title=title,
        category=category,
        salary=salary,
        full=full,
        location=location,
        company=company,
        skills=skills,
        schedule_type=schedule_type,
        work_from_home=work_from_home,
    )