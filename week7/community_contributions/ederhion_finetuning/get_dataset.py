import os
from pydantic import BaseModel
from datasets import load_dataset, Dataset, DatasetDict
from transformers import AutoTokenizer
from typing import Optional, Self
from tqdm.auto import tqdm
from dotenv import load_dotenv
from huggingface_hub import login

# Load environment variables (make sure HF_TOKEN is in your .env file)
load_dotenv(override=True)
hf_token = os.environ.get('HF_TOKEN')

if hf_token:
    print("Logging in to Hugging Face...")
    login(hf_token, add_to_git_credential=True)
else:
    raise ValueError("HF_TOKEN not found in environment. Please add it to your .env file.")

# We use a similar prompt structure to the Week 7 capstone
PREFIX = "Salary is $"
QUESTION = "What is the annual salary for this role to the nearest dollar?"

class JobItem(BaseModel):
    """
    A JobItem represents a single job posting with its title, description, and target salary.
    """
    title: str
    description: str
    salary: float
    prompt: Optional[str] = None
    completion: Optional[str] = None

    def make_prompts(self, tokenizer, max_tokens: int, do_round: bool):
        """
        Truncates the job description to the max_tokens limit and formats the prompt.
        """
        # Count tokens in the description
        tokens = tokenizer.encode(self.description, add_special_tokens=False)
        
        # Truncate if the job description is too long
        if len(tokens) > max_tokens:
            description = tokenizer.decode(tokens[:max_tokens]).rstrip()
        else:
            description = self.description
            
        # Format the prompt and completion
        self.prompt = f"{QUESTION}\n\nTitle: {self.title}\n\nDescription:\n{description}\n\n{PREFIX}"
        self.completion = f"{round(self.salary)}.00" if do_round else str(self.salary)

    def to_datapoint(self) -> dict:
        """Converts the object into a dictionary for the Hugging Face dataset."""
        return {"prompt": self.prompt, "completion": self.completion}

def process_job_dataset(dataset_name: str, model_name: str, max_tokens: int = 150):
    """
    Loads a Hugging Face dataset, filters for valid salaries, and formats it for Large Language Model (LLM) training.
    """
    print(f"Loading dataset: {dataset_name}")
    # Load the raw dataset from Hugging Face
    raw_dataset = load_dataset(dataset_name, split="train")
    
    # Filter out rows that don't have a valid salary
    # (Adjust 'salary_year_avg' based on the specific Hugging Face dataset's column names)
    valid_jobs = raw_dataset.filter(lambda x: x["salary_year_avg"] is not None)
    print(f"Found {len(valid_jobs)} jobs with valid annual salaries.")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    processed_items = []

    print("Formatting prompts and truncating long descriptions...")
    for row in tqdm(valid_jobs):
        # Handle cases where the role involves working remotely
        title_context = f"{row['job_title_short']} (Remote)" if row.get("job_work_from_home") else row['job_title_short']
        
        # Build a synthetic description from available parsed fields
        skills = row.get("job_skills")
        if isinstance(skills, list):
            skills_str = ", ".join(skills)
        elif skills:
            skills_str = str(skills)
        else:
            skills_str = "Not specified"
            
        company = row.get("company_name") or "Unknown Company"
        schedule = row.get("job_schedule_type") or "Unknown Schedule"
        
        constructed_description = (
            f"Company: {company}\n"
            f"Schedule: {schedule}\n"
            f"Required Skills: {skills_str}"
        )
        
        item = JobItem(
            title=title_context,
            description=constructed_description,
            salary=float(row["salary_year_avg"])
        )
        
        # Apply truncation and formatting, rounding the target salary
        item.make_prompts(tokenizer, max_tokens=max_tokens, do_round=True)
        processed_items.append(item.to_datapoint())

    # Convert back to a Hugging Face Dataset format
    final_dataset = Dataset.from_list(processed_items)
    
    # Split into Train and Test sets (90% / 10%)
    train_test_split = final_dataset.train_test_split(test_size=0.1)
    
    return train_test_split

if __name__ == "__main__":
    # Ensure you are logged in to Hugging Face via the CLI (Command Line Interface)
    # or by setting the HF_TOKEN environment variable.
    
    DATASET_SOURCE = "lukebarousse/data_jobs"
    BASE_MODEL = "meta-llama/Llama-3.2-3B"
    HF_USERNAME = "jederhion"
    
    # 1. Process the raw data into prompt/completion pairs
    ready_to_train_data = process_job_dataset(DATASET_SOURCE, BASE_MODEL, max_tokens=200)
    
    # 2. Push the processed datasets to your Hugging Face Hub for fine-tuning
    output_repo = f"{HF_USERNAME}/job_salary_prompts"
    print(f"Pushing processed dataset to {output_repo}...")
    ready_to_train_data.push_to_hub(output_repo)
    print("Done!")