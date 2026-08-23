import os
import re
import torch
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from tqdm import tqdm
from sklearn.metrics import mean_squared_error, r2_score
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from dotenv import load_dotenv
from huggingface_hub import login

# 1. Authenticate with Hugging Face
load_dotenv(override=True)
hf_token = os.environ.get('HF_TOKEN')
if hf_token:
    login(hf_token, add_to_git_credential=True)
else:
    raise ValueError("HF_TOKEN not found in environment.")

# Configuration
BASE_MODEL = "meta-llama/Llama-3.2-3B"
ADAPTER_REPO = "jederhion/job_salary_adapters"
DATASET_ID = "jederhion/job_salary_prompts"
SAMPLE_SIZE = 100 # Number of test cases to evaluate

def extract_number(text: str) -> float:
    """Extracts the first numeric value found in the generated string."""
    text = text.replace(",", "")
    match = re.search(r"[-+]?\d*\.\d+|\d+", text)
    return float(match.group()) if match else 0.0

def evaluate():
    print("Loading test dataset...")
    # Load just the test split
    dataset = load_dataset(DATASET_ID, split="test")
    # Take a random sample to speed up evaluation
    test_data = dataset.shuffle(seed=42).select(range(min(SAMPLE_SIZE, len(dataset))))

    print("Loading base model and tokenizer onto Apple Silicon (MPS)...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    # Load base model in 16-bit precision optimized for Mac
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="mps"
    )

    print(f"Applying fine-tuned adapters from {ADAPTER_REPO}...")
    model = PeftModel.from_pretrained(base_model, ADAPTER_REPO)
    model.eval() # Set to evaluation mode

    truths = []
    guesses = []
    errors = []

    print(f"Starting inference on {SAMPLE_SIZE} job postings...")
    for item in tqdm(test_data):
        prompt = item["prompt"]
        truth = float(item["completion"])
        
        # Format input for the model
        inputs = tokenizer(prompt, return_tensors="pt").to("mps")
        
        # Generate the prediction (we only need a few tokens for the price)
        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_new_tokens=10, 
                pad_token_id=tokenizer.eos_token_id,
                do_sample=False
            )
        
        # Decode the output, stripping away the original prompt
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]
        generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        guess = extract_number(generated_text)
        error = abs(guess - truth)
        
        truths.append(truth)
        guesses.append(guess)
        errors.append(error)

    # Calculate final metrics
    avg_error = sum(errors) / len(errors)
    mse = mean_squared_error(truths, guesses)
    r2 = r2_score(truths, guesses) * 100

    print("\n" + "="*40)
    print("EVALUATION RESULTS")
    print("="*40)
    print(f"Average Absolute Error: ${avg_error:,.2f}")
    print(f"Mean Squared Error (MSE): {mse:,.0f}")
    print(f"R-squared (R²): {r2:.1f}%")

    # Plot the results
    plot_results(truths, guesses, avg_error, mse, r2)

def plot_results(truths, guesses, avg_error, mse, r2):
    """Generates a scatter plot comparing actual vs. predicted salaries."""
    df = pd.DataFrame({"Actual": truths, "Predicted": guesses})
    
    # Assign colors based on error margins
    df["Error"] = abs(df["Actual"] - df["Predicted"])
    df["Color"] = df.apply(lambda row: "green" if row["Error"] < 10000 else ("orange" if row["Error"] < 25000 else "red"), axis=1)

    max_val = max(df["Actual"].max(), df["Predicted"].max())

    fig = px.scatter(
        df, x="Actual", y="Predicted", color="Color",
        color_discrete_map={"green": "green", "orange": "orange", "red": "red"},
        title=f"Job Salary Predictions<br><b>Avg Error:</b> ${avg_error:,.0f} | <b>R²:</b> {r2:.1f}%",
        labels={"Actual": "Actual Salary ($)", "Predicted": "Predicted Salary ($)"},
        width=800, height=600
    )

    # Reference line y=x (Perfect predictions)
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val], mode="lines",
        line=dict(width=2, dash="dash", color="deepskyblue"),
        name="Perfect Prediction", showlegend=False
    ))

    fig.update_xaxes(range=[0, max_val])
    fig.update_yaxes(range=[0, max_val])
    fig.update_layout(showlegend=False)
    fig.show()

if __name__ == "__main__":
    evaluate()