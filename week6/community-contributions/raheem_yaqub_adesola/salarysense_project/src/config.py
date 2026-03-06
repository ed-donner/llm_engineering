import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gpt-4.1-nano"

TRAIN_SPLIT = 0.8
VAL_SPLIT = 0.1
TEST_SPLIT = 0.1

DATASET_NAME = "ruchi798/data-science-job-salaries"

PRICE_PREFIX = "Salary is $"
QUESTION = "What is the expected salary for this job?"
