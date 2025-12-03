"""
AI-Powered Test Data Generator

Generate realistic test data for testing, development, and prototyping using open-source LLMs.
Uses HuggingFace Inference API for cloud-based model inference.
"""

import gradio as gr
from huggingface_hub import InferenceClient
import pandas as pd
import json
import csv
import io
import re
import tempfile
import os

# Available HuggingFace models for inference
AVAILABLE_MODELS = [
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
    "google/gemma-2-9b-it",
]

# Predefined data templates
DATA_TEMPLATES = {
    "Users": {
        "fields": ["id", "first_name", "last_name", "email", "phone", "address", "city", "country", "created_at"],
        "description": "User profile data with contact information"
    },
    "Products": {
        "fields": ["id", "name", "description", "category", "price", "stock_quantity", "sku", "brand", "rating"],
        "description": "E-commerce product catalog data"
    },
    "Orders": {
        "fields": ["order_id", "customer_id", "product_id", "quantity", "unit_price", "total_amount", "status", "order_date", "shipping_address"],
        "description": "Order transaction data"
    },
    "Employees": {
        "fields": ["employee_id", "first_name", "last_name", "email", "department", "job_title", "salary", "hire_date", "manager_id"],
        "description": "Employee HR data"
    },
    "Transactions": {
        "fields": ["transaction_id", "account_id", "transaction_type", "amount", "currency", "timestamp", "status", "description"],
        "description": "Financial transaction records"
    },
    "Reviews": {
        "fields": ["review_id", "product_id", "user_id", "rating", "title", "comment", "helpful_votes", "verified_purchase", "review_date"],
        "description": "Product review data"
    },
    "Custom": {
        "fields": [],
        "description": "Define your own schema"
    }
}


def get_hf_client():
    """Get HuggingFace Inference client."""
    token = os.environ.get("HF_TOKEN")
    return InferenceClient(token=token)


def parse_json_from_response(response: str) -> list:
    """Extract JSON array from LLM response."""
    text = response.strip()

    # Method 1: Try parsing the entire response as JSON first
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Method 2: Extract from markdown code blocks
    code_block_patterns = [
        r'```json\s*\n?([\s\S]*?)\n?```',
        r'```\s*\n?([\s\S]*?)\n?```',
    ]

    for pattern in code_block_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                continue

    # Method 3: Find JSON array by bracket matching
    start_idx = text.find('[')
    if start_idx != -1:
        bracket_count = 0
        end_idx = start_idx

        for i, char in enumerate(text[start_idx:], start=start_idx):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i
                    break

        if end_idx > start_idx:
            json_str = text[start_idx:end_idx + 1]
            try:
                result = json.loads(json_str)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

    # Method 4: Try to fix common JSON issues and parse again
    cleaned = re.sub(r',\s*([}\]])', r'\1', text)
    start_idx = cleaned.find('[')
    if start_idx != -1:
        bracket_count = 0
        end_idx = start_idx

        for i, char in enumerate(cleaned[start_idx:], start=start_idx):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i
                    break

        if end_idx > start_idx:
            json_str = cleaned[start_idx:end_idx + 1]
            try:
                result = json.loads(json_str)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

    return []


def generate_data_with_llm(
    model: str,
    data_type: str,
    fields: list,
    num_records: int,
    custom_instructions: str = "",
    locale: str = "en_US"
) -> tuple[list, str]:
    """Generate test data using HuggingFace Inference API."""

    fields_str = ", ".join(fields)

    prompt = f"""Generate exactly {num_records} realistic test data records for {data_type}.

Required fields: {fields_str}

Requirements:
- Return ONLY a valid JSON array with {num_records} objects
- Each object must have all the specified fields
- Use realistic, varied data
- Locale preference: {locale}
{f'- Additional instructions: {custom_instructions}' if custom_instructions else ''}

IMPORTANT: Return ONLY the JSON array, no explanations, no markdown code blocks, just the raw JSON array starting with [ and ending with ]."""

    try:
        client = get_hf_client()

        response = client.chat_completion(
            model=model,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            max_tokens=4096,
            temperature=0.7
        )

        response_text = response.choices[0].message.content
        data = parse_json_from_response(response_text)

        if not data:
            return [], "Error: Failed to parse LLM response as JSON. Please try again."

        if len(data) > num_records:
            data = data[:num_records]

        return data, f"Successfully generated {len(data)} records using {model.split('/')[-1]}"

    except Exception as e:
        return [], f"Error generating data: {str(e)}"


def export_to_csv(data: list) -> str:
    """Convert data to CSV string."""
    if not data:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def export_to_json(data: list, pretty: bool = True) -> str:
    """Convert data to JSON string."""
    if pretty:
        return json.dumps(data, indent=2, default=str)
    return json.dumps(data, default=str)


def save_to_file(content: str, filename: str) -> str:
    """Save content to a temporary file and return the path."""
    if not content:
        return None
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath


# Global variable to store generated data
current_data = []


def update_fields(data_type: str) -> str:
    """Update fields textbox based on selected data type."""
    if data_type in DATA_TEMPLATES:
        return ", ".join(DATA_TEMPLATES[data_type]["fields"])
    return ""


def generate_data(
    model: str,
    data_type: str,
    fields_str: str,
    num_records: int,
    custom_instructions: str,
    locale: str,
    progress=gr.Progress()
):
    """Main function to generate test data."""
    global current_data

    progress(0, desc="Starting generation...")

    fields = [f.strip() for f in fields_str.split(",") if f.strip()]

    if not fields:
        return "Error: No fields specified", None, None, None

    if num_records < 1 or num_records > 1000:
        return "Error: Number of records must be between 1 and 1000", None, None, None

    progress(0.3, desc="Generating data with LLM...")

    data, status = generate_data_with_llm(
        model=model,
        data_type=data_type,
        fields=fields,
        num_records=int(num_records),
        custom_instructions=custom_instructions,
        locale=locale
    )

    if not data:
        return status, None, None, None

    current_data = data

    progress(0.7, desc="Formatting output...")

    df = pd.DataFrame(data)

    csv_content = export_to_csv(data)
    json_content = export_to_json(data)

    csv_file = save_to_file(csv_content, f"{data_type.lower()}_data.csv")
    json_file = save_to_file(json_content, f"{data_type.lower()}_data.json")

    progress(1.0, desc="Complete!")

    return status, df, csv_file, json_file


def create_custom_data(
    model: str,
    schema_json: str,
    num_records: int,
    context: str,
    progress=gr.Progress()
):
    """Generate data from custom JSON schema."""
    global current_data

    progress(0, desc="Parsing schema...")

    try:
        schema = json.loads(schema_json)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON schema - {str(e)}", None, None, None

    if not isinstance(schema, dict):
        return "Error: Schema must be a JSON object with field definitions", None, None, None

    fields = list(schema.keys())

    schema_description = "\n".join([f"- {k}: {v}" for k, v in schema.items()])
    custom_instructions = f"""Field specifications:
{schema_description}

Context: {context if context else 'General test data'}"""

    progress(0.3, desc="Generating data with LLM...")

    data, status = generate_data_with_llm(
        model=model,
        data_type="Custom",
        fields=fields,
        num_records=int(num_records),
        custom_instructions=custom_instructions
    )

    if not data:
        return status, None, None, None

    current_data = data

    progress(0.7, desc="Formatting output...")

    df = pd.DataFrame(data)

    csv_content = export_to_csv(data)
    json_content = export_to_json(data)

    csv_file = save_to_file(csv_content, "custom_data.csv")
    json_file = save_to_file(json_content, "custom_data.json")

    progress(1.0, desc="Complete!")

    return status, df, csv_file, json_file


# Build the Gradio interface
with gr.Blocks(
    title="AI Test Data Generator",
    theme=gr.themes.Soft(),
    css="""
    .container { max-width: 1200px; margin: auto; }
    .header { text-align: center; margin-bottom: 20px; }
    """
) as demo:

    gr.Markdown(
        """
        # AI-Powered Test Data Generator

        Generate realistic test data using open-source LLMs via HuggingFace Inference API.
        Choose from predefined templates or create custom schemas.

        **Note:** For best results, set your `HF_TOKEN` environment variable. Get your free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
        """
    )

    with gr.Tabs():
        # Tab 1: Template-based Generation
        with gr.Tab("Template Generator"):
            with gr.Row():
                with gr.Column(scale=1):
                    model_dropdown = gr.Dropdown(
                        choices=AVAILABLE_MODELS,
                        value=AVAILABLE_MODELS[0],
                        label="LLM Model",
                        info="Select the HuggingFace model to use"
                    )

                    data_type_dropdown = gr.Dropdown(
                        choices=list(DATA_TEMPLATES.keys()),
                        value="Users",
                        label="Data Type",
                        info="Select a predefined template"
                    )

                    fields_input = gr.Textbox(
                        value=", ".join(DATA_TEMPLATES["Users"]["fields"]),
                        label="Fields (comma-separated)",
                        info="Customize the fields to generate",
                        lines=2
                    )

                    num_records_slider = gr.Slider(
                        minimum=1,
                        maximum=100,
                        value=10,
                        step=1,
                        label="Number of Records"
                    )

                    locale_dropdown = gr.Dropdown(
                        choices=["en_US", "en_GB", "de_DE", "fr_FR", "es_ES", "it_IT", "ja_JP", "zh_CN", "pt_BR", "in_IN"],
                        value="en_US",
                        label="Locale",
                        info="Regional format for generated data"
                    )

                    custom_instructions_input = gr.Textbox(
                        label="Custom Instructions (optional)",
                        placeholder="e.g., 'Include only tech companies', 'Use prices in EUR'",
                        lines=2
                    )

                    generate_btn = gr.Button("Generate Data", variant="primary", size="lg")

                with gr.Column(scale=2):
                    status_output = gr.Textbox(label="Status", interactive=False)
                    data_output = gr.Dataframe(
                        label="Generated Data",
                        interactive=False,
                        wrap=True
                    )

                    with gr.Row():
                        csv_download = gr.File(label="Download CSV")
                        json_download = gr.File(label="Download JSON")

            data_type_dropdown.change(
                fn=update_fields,
                inputs=[data_type_dropdown],
                outputs=[fields_input]
            )

            generate_btn.click(
                fn=generate_data,
                inputs=[
                    model_dropdown,
                    data_type_dropdown,
                    fields_input,
                    num_records_slider,
                    custom_instructions_input,
                    locale_dropdown
                ],
                outputs=[
                    status_output,
                    data_output,
                    csv_download,
                    json_download
                ]
            )

        # Tab 2: Custom Schema Generator
        with gr.Tab("Custom Schema"):
            with gr.Row():
                with gr.Column(scale=1):
                    custom_model_dropdown = gr.Dropdown(
                        choices=AVAILABLE_MODELS,
                        value=AVAILABLE_MODELS[0],
                        label="LLM Model"
                    )

                    schema_input = gr.Code(
                        value="""{
    "id": "unique integer identifier",
    "company_name": "realistic company name",
    "industry": "industry sector",
    "revenue": "annual revenue in millions USD",
    "employees": "number of employees",
    "founded_year": "year company was founded",
    "headquarters": "city and country",
    "is_public": "boolean - publicly traded"
}""",
                        language="json",
                        label="Schema Definition (JSON)",
                        lines=12
                    )

                    custom_num_records = gr.Slider(
                        minimum=1,
                        maximum=100,
                        value=10,
                        step=1,
                        label="Number of Records"
                    )

                    context_input = gr.Textbox(
                        label="Context/Domain (optional)",
                        placeholder="e.g., 'Healthcare industry', 'E-commerce platform'",
                        lines=2
                    )

                    custom_generate_btn = gr.Button("Generate Custom Data", variant="primary", size="lg")

                with gr.Column(scale=2):
                    custom_status_output = gr.Textbox(label="Status", interactive=False)
                    custom_data_output = gr.Dataframe(
                        label="Generated Data",
                        interactive=False,
                        wrap=True
                    )

                    with gr.Row():
                        custom_csv_download = gr.File(label="Download CSV")
                        custom_json_download = gr.File(label="Download JSON")

            custom_generate_btn.click(
                fn=create_custom_data,
                inputs=[
                    custom_model_dropdown,
                    schema_input,
                    custom_num_records,
                    context_input
                ],
                outputs=[
                    custom_status_output,
                    custom_data_output,
                    custom_csv_download,
                    custom_json_download
                ]
            )

        # Tab 3: Help & Examples
        with gr.Tab("Help & Examples"):
            gr.Markdown(
                """
                ## How to Use

                ### Setup

                **For HuggingFace Spaces:**
                - The app uses HuggingFace Inference API
                - Set `HF_TOKEN` as a Space secret for higher rate limits
                - Get your free token at: https://huggingface.co/settings/tokens

                **For Local Use:**
                - Set environment variable: `export HF_TOKEN=your_token_here`
                - Or create a `.env` file with `HF_TOKEN=your_token_here`

                ### Template Generator
                1. Select an LLM model from the dropdown
                2. Choose a data type template (Users, Products, Orders, etc.)
                3. Customize fields if needed
                4. Set the number of records to generate
                5. Optionally add custom instructions for more specific data
                6. Click "Generate Data"

                ### Custom Schema
                1. Define your schema as a JSON object
                2. Each key is a field name, each value describes what data to generate
                3. Add context to help the LLM understand the domain

                ### Example Custom Schemas

                **IoT Sensor Data:**
                ```json
                {
                    "sensor_id": "unique sensor identifier",
                    "device_type": "temperature, humidity, or pressure sensor",
                    "reading": "numeric sensor reading",
                    "unit": "measurement unit",
                    "timestamp": "ISO format datetime",
                    "location": "building and room identifier",
                    "battery_level": "percentage 0-100"
                }
                ```

                **Medical Records:**
                ```json
                {
                    "patient_id": "unique identifier",
                    "diagnosis_code": "ICD-10 code",
                    "diagnosis_description": "medical condition",
                    "visit_date": "date of visit",
                    "physician": "doctor name",
                    "department": "hospital department",
                    "treatment_plan": "brief treatment description"
                }
                ```

                **Event Logs:**
                ```json
                {
                    "event_id": "unique event identifier",
                    "event_type": "login, logout, purchase, error",
                    "user_id": "user identifier",
                    "timestamp": "ISO datetime",
                    "ip_address": "IPv4 address",
                    "user_agent": "browser user agent string",
                    "status": "success or failure",
                    "metadata": "additional JSON data"
                }
                ```

                ### Tips

                - For best results, use descriptive field names
                - Add custom instructions for domain-specific data
                - Larger models (Qwen2.5-72B, Llama-3.1-8B) produce better quality but are slower
                """
            )

    gr.Markdown(
        """
        ---
        Built with Gradio and HuggingFace | Open Source Test Data Generator
        """
    )


if __name__ == "__main__":
    demo.launch()
