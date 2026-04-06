"""Streamlit UI for Synthetic Data Generator."""

import sys
from pathlib import Path

# Add parent directory to path for package imports when run directly
if __name__ == "__main__" or "streamlit" in sys.modules:
    parent_dir = Path(__file__).parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Use absolute imports for Streamlit compatibility
from synth_data.backends.huggingface_api import HuggingFaceAPIBackend
from synth_data.backends.base import GenerationParams
from synth_data.services.generator import GeneratorService
from synth_data.services.export import ExportService, ExportFormat
from synth_data.database.service import DatabaseService
from synth_data.utils.schema_parser import parse_schema, format_schema_for_display
from synth_data.exceptions import SchemaValidationError, APIKeyError, GenerationError
from synth_data.config import settings, configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon=settings.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Model options with descriptions
MODEL_OPTIONS = {
    "Qwen/Qwen2.5-Coder-32B-Instruct": "Best for structured data (Default)",
    "meta-llama/Llama-3.1-8B-Instruct": "Faster, good for simple schemas",
    "mistralai/Mistral-7B-Instruct-v0.3": "Balanced performance"
}


def init_session_state():
    """Initialize Streamlit session state."""
    if 'api_key' not in st.session_state:
        st.session_state.api_key = settings.HUGGINGFACE_API_KEY or ""
    if 'api_key_manual_override' not in st.session_state:
        st.session_state.api_key_manual_override = False
    if 'generated_data' not in st.session_state:
        st.session_state.generated_data = None
    if 'current_generation_id' not in st.session_state:
        st.session_state.current_generation_id = None
    if 'viewing_historical' not in st.session_state:
        st.session_state.viewing_historical = False
    if 'generation_metadata' not in st.session_state:
        st.session_state.generation_metadata = {}
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = list(MODEL_OPTIONS.keys())[0]
    if 'schema_input_manual' not in st.session_state:
        st.session_state.schema_input_manual = ""


def render_api_key_input() -> Optional[str]:
    """Render API key input field."""
    st.subheader("🔑 API Configuration")

    # Check if API key was loaded from .env
    env_api_key = settings.HUGGINGFACE_API_KEY
    has_env_key = env_api_key and len(env_api_key) > 0

    if has_env_key:
        # Show checkbox to override .env key
        use_different_key = st.checkbox(
            "Use a different API key (override .env)",
            value=st.session_state.get('api_key_manual_override', False),
            key="override_env_key",
            help="Check this to enter a different API key instead of using the one from .env"
        )

        # Update session state
        st.session_state.api_key_manual_override = use_different_key

        if not use_different_key:
            # Using .env key - show success message
            st.success("✅ API key loaded successfully from .env file")
            st.caption(f"🔒 Token: {env_api_key[:7]}...{env_api_key[-4:]} (masked for security)")

            # Use the env key
            st.session_state.api_key = env_api_key
            return env_api_key
        else:
            # User wants to override - show password input
            st.info("💡 Enter your API key below to override the .env configuration")

    # Show password input (either no env key or user wants to override)
    api_key = st.text_input(
        "HuggingFace API Key",
        value="" if not st.session_state.api_key or has_env_key else st.session_state.api_key,
        type="password",
        help="Enter your HuggingFace API key (will be hidden for security)",
        placeholder="hf_...",
        key="api_key_input"
    )

    if api_key and api_key != st.session_state.api_key:
        st.session_state.api_key = api_key

    if not api_key:
        st.warning("⚠️ Please enter your API key to continue")
        st.info("Get your free API key at: https://huggingface.co/settings/tokens")
        return None

    return api_key


def render_model_selection() -> str:
    """
    Render model selection dropdown.

    Returns:
        Selected model ID
    """
    st.subheader("🤖 Model Selection")

    model_display = [f"{model} - {desc}" for model, desc in MODEL_OPTIONS.items()]
    selected_display = st.selectbox(
        "Model",
        options=model_display,
        index=0,
        help="Select the LLM model to use for generation"
    )

    # Extract model ID from display string
    model_id = selected_display.split(" - ")[0]

    # Store in session state for schema generation
    st.session_state.selected_model = model_id

    return model_id


def generate_schema_from_description(description: str, api_key: str, model_id: str) -> Optional[str]:
    """
    Use LLM to generate schema from natural language description.

    Args:
        description: Natural language description of desired data
        api_key: HuggingFace API key
        model_id: Model to use

    Returns:
        Generated schema string (JSON or simplified format), or None if failed
    """
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://router.huggingface.co/v1/"
        )

        prompt = f"""Based on this description, generate a JSON schema for synthetic data generation:

"{description}"

Requirements:
- Return ONLY a valid JSON schema object
- Use appropriate data types: string, integer, number, boolean, array
- Include reasonable constraints (minimum, maximum, etc.) where applicable
- Make it practical and realistic
- No explanations, just the JSON schema

Example format:
{{
    "name": {{"type": "string"}},
    "age": {{"type": "integer", "minimum": 18, "maximum": 65}},
    "email": {{"type": "string"}}
}}"""

        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": "You are a data schema expert. Generate clean, valid JSON schemas without any extra text or explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1000
        )

        schema_str = response.choices[0].message.content.strip()

        # Clean up markdown code blocks if present
        if schema_str.startswith("```"):
            lines = schema_str.split("\n")
            lines = lines[1:]  # Remove opening ```
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]  # Remove closing ```
            schema_str = "\n".join(lines).strip()

        # Find JSON object
        start_idx = schema_str.find("{")
        end_idx = schema_str.rfind("}")
        if start_idx != -1 and end_idx != -1:
            schema_str = schema_str[start_idx:end_idx + 1]

        return schema_str

    except Exception as e:
        st.error(f"Failed to generate schema: {str(e)}")
        logger.error(f"Schema generation failed: {e}", exc_info=True)
        return None


def render_schema_input() -> Optional[Dict[str, Any]]:
    """
    Render schema input section with natural language description option.

    Returns:
        Parsed schema dictionary, or None if invalid
    """
    st.subheader("⚙️ Schema Definition")

    # Create tabs for different input methods
    input_tab1, input_tab2 = st.tabs(["🗣️ Describe Your Data", "⚙️ Manual Schema"])

    with input_tab1:
        st.markdown("**Describe the data you need in plain English:**")

        description = st.text_area(
            "Data Description",
            placeholder="Example: Employee records with name, age, department, salary, hire date, and email address",
            height=100,
            key="data_description",
            label_visibility="collapsed"
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_schema_btn = st.button(
                "✨ Generate Schema from Description",
                type="secondary",
                use_container_width=True,
                disabled=not description.strip()
            )

        if generate_schema_btn and description.strip():
            # Need API key to generate schema
            if not st.session_state.api_key:
                st.error("⚠️ Please enter your API key first (in the section above)")
                return None

            with st.spinner("Generating schema from your description..."):
                # Get current model selection from session state or use default
                model_id = st.session_state.get('selected_model', list(MODEL_OPTIONS.keys())[0])

                generated_schema = generate_schema_from_description(
                    description,
                    st.session_state.api_key,
                    model_id
                )

                if generated_schema:
                    # Update the widget state directly - this is the source of truth
                    st.session_state.schema_input_manual = generated_schema
                    st.success("✅ Schema generated! Review and edit below if needed.")
                    st.rerun()

        # Show example
        with st.expander("💡 Example Descriptions"):
            st.markdown("""
            - "Customer records with name, email, phone number, address, and purchase history"
            - "Product catalog with SKU, name, description, price, category, and stock quantity"
            - "Student records with ID, name, grade level, GPA, and enrollment date"
            - "Employee data including name, job title, department, salary, and years of experience"
            - "E-commerce orders with order ID, customer info, items, total price, and delivery status"
            """)

    with input_tab2:
        # Show format help
        with st.expander("ℹ️ Schema Format Help", expanded=False):
            st.markdown("""
            **Two formats supported:**

            **1. JSON Format (Full control):**
            ```json
            {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 18, "maximum": 65},
                "email": {"type": "string"}
            }
            ```

            **2. Simplified Format (Quick and easy):**
            ```
            name:string, age:integer, email:string
            ```

            **Supported types:** `string`, `integer`, `number`, `boolean`, `array`

            **Type aliases:** `str`, `int`, `float`, `bool`, `list`
            """)

        # Schema input - manual entry
        # The widget automatically stores its value in st.session_state.schema_input_manual
        schema_input_manual = st.text_area(
            "Enter schema (JSON or simplified format)",
            height=150,
            placeholder='name:string, age:integer, email:string\n\nor\n\n{"name": {"type": "string"}, "age": {"type": "integer"}}',
            key="schema_input_manual"
        )

    # Parse and validate schema (whether from manual input or generated)
    # The widget state is the source of truth
    schema_to_parse = st.session_state.get('schema_input_manual', '')

    if not schema_to_parse or not schema_to_parse.strip():
        st.info("👆 Please describe your data or enter a schema manually to get started")
        return None

    # Try to parse schema
    try:
        schema = parse_schema(schema_to_parse)

        # Show parsed schema below the tabs
        st.markdown("---")
        formatted = format_schema_for_display(schema)
        st.success(f"✅ **Ready to generate:** {formatted}")
        return schema

    except SchemaValidationError as e:
        st.error(f"❌ Schema validation failed: {str(e)}")
        st.info("💡 Try using the 'Describe Your Data' tab and let the AI generate the schema for you!")
        return None


def render_generation_params() -> tuple[int, GenerationParams]:
    """
    Render generation parameters inputs.

    Returns:
        Tuple of (num_records, GenerationParams)
    """
    col1, col2 = st.columns(2)

    with col1:
        num_records = st.slider(
            "Number of Records",
            min_value=1,
            max_value=100,
            value=10,
            help="Number of synthetic records to generate (1-100 for MVP)"
        )

    with col2:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Higher = more creative/random, Lower = more focused/deterministic"
        )

    params = GenerationParams(
        temperature=temperature,
        max_tokens=settings.DEFAULT_MAX_TOKENS
    )

    return num_records, params


def generate_data(
    api_key: str,
    model_id: str,
    schema: Dict[str, Any],
    num_records: int,
    params: GenerationParams
) -> Optional[Dict[str, Any]]:
    """
    Generate synthetic data.

    Args:
        api_key: HuggingFace API key
        model_id: Model to use
        schema: Schema dictionary
        num_records: Number of records
        params: Generation parameters

    Returns:
        Generation result dictionary, or None if failed
    """
    try:
        # Create backend
        backend = HuggingFaceAPIBackend(
            api_key=api_key,
            model_id=model_id
        )

        # Create service with database
        service = GeneratorService(backend=backend, save_to_db=True)

        # Generate with progress
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_callback(current: int, total: int):
            progress = min(current / total, 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Generating... {current}/{total} records")

        # Call generation
        result = service.generate(
            schema=schema,
            num_records=num_records,
            params=params,
            on_progress=progress_callback
        )

        progress_bar.progress(1.0)
        status_text.text("Generation complete!")

        # Clean up
        service.close()

        return result

    except APIKeyError as e:
        st.error(f"❌ Invalid API key: {str(e)}")
        st.info("💡 Check your HuggingFace API key and try again")
        return None

    except SchemaValidationError as e:
        st.error(f"❌ Schema validation failed: {str(e)}")
        st.info("💡 Review your schema format and ensure all fields are valid")
        return None

    except GenerationError as e:
        st.error(f"❌ Generation failed: {str(e)}")
        st.info("💡 Try reducing the number of records or simplifying the schema")
        return None

    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        logger.error(f"Unexpected error during generation: {e}", exc_info=True)
        return None


def render_results(result: Dict[str, Any]):
    """
    Render generation results.

    Args:
        result: Generation result dictionary
    """
    st.subheader("📊 Results")

    if not result['success']:
        st.error(f"❌ Generation failed: {result['error_message']}")
        return

    # Success message with metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Records Generated", result['num_records'])
    with col2:
        st.metric("Backend", result['backend'])
    with col3:
        if st.session_state.generation_metadata.get('duration'):
            duration = st.session_state.generation_metadata['duration']
            st.metric("Duration", f"{duration:.1f}s")

    # Show data preview
    st.markdown("### Data Preview")
    df = pd.DataFrame(result['data'])
    st.dataframe(df, use_container_width=True, height=400)

    # Download button
    st.markdown("### Export")
    export_service = ExportService()

    col1, col2, col3 = st.columns(3)

    with col1:
        csv_data = export_service.to_csv(result['data'])
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=export_service.suggest_filename(ExportFormat.CSV),
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        json_data = export_service.to_json(result['data'], pretty=True)
        st.download_button(
            label="⬇️ Download JSON",
            data=json_data,
            file_name=export_service.suggest_filename(ExportFormat.JSON),
            mime="application/json",
            use_container_width=True
        )

    with col3:
        jsonl_data = export_service.to_jsonl(result['data'])
        st.download_button(
            label="⬇️ Download JSONL",
            data=jsonl_data,
            file_name=export_service.suggest_filename(ExportFormat.JSONL),
            mime="application/jsonl",
            use_container_width=True
        )


def render_generate_tab():
    """Render the main generation tab."""
    st.title("📊 Synthetic Data Generator MVP")
    st.markdown("Generate synthetic data using LLM APIs")

    st.markdown("---")

    # API Key
    api_key = render_api_key_input()
    if not api_key:
        return

    st.markdown("---")

    # Model Selection
    model_id = render_model_selection()

    st.markdown("---")

    # Schema Input
    schema = render_schema_input()

    st.markdown("---")

    # Generation Parameters
    num_records, params = render_generation_params()

    st.markdown("---")

    # Generate Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button(
            "🚀 Generate Data",
            type="primary",
            use_container_width=True,
            disabled=(schema is None)
        )

    if generate_button and schema:
        st.markdown("---")

        with st.spinner("Generating data..."):
            start_time = datetime.now()
            result = generate_data(api_key, model_id, schema, num_records, params)
            end_time = datetime.now()

            if result:
                duration = (end_time - start_time).total_seconds()
                st.session_state.generation_metadata = {'duration': duration}
                st.session_state.generated_data = result
                st.session_state.current_generation_id = result.get('generation_id')
                st.session_state.viewing_historical = False

    # Show results if available
    if st.session_state.generated_data and not st.session_state.viewing_historical:
        st.markdown("---")
        render_results(st.session_state.generated_data)

    # Show historical data if viewing
    if st.session_state.viewing_historical and st.session_state.generated_data:
        st.markdown("---")
        st.info("📜 Viewing historical generation")
        render_results(st.session_state.generated_data)

        if st.button("🔄 Clear and Generate New"):
            st.session_state.viewing_historical = False
            st.session_state.generated_data = None
            st.rerun()


def render_history_tab():
    """Render the history tab."""
    st.title("📜 Generation History")
    st.markdown("Browse and manage past generations")

    st.markdown("---")

    # Initialize database service
    db = DatabaseService()

    # Get all generations
    generations = db.get_all_generations()

    if not generations:
        st.info("No generations yet. Go to the Generate tab to create your first dataset!")
        return

    st.markdown(f"**Total Generations:** {len(generations)}")

    # Filters
    st.subheader("🔍 Filters")
    col1, col2 = st.columns(2)

    with col1:
        # Get unique model backends
        unique_backends = list(set(g.model_backend for g in generations))

        # Parse and display model IDs for better UX
        display_backends = []
        for backend in unique_backends:
            if ":" in backend:
                _, model_id = backend.split(":", 1)
                display_backends.append(model_id)
            else:
                display_backends.append(backend)

        filter_display = st.selectbox(
            "Model",
            options=["All Models"] + display_backends,
            key="filter_backend"
        )

        # Map back to full backend string
        if filter_display != "All Models":
            # Find the full backend string that matches this display
            filter_backend = None
            for backend in unique_backends:
                if ":" in backend and backend.split(":", 1)[1] == filter_display:
                    filter_backend = backend
                    break
                elif backend == filter_display:
                    filter_backend = backend
                    break
        else:
            filter_backend = "All Models"

    with col2:
        filter_status = st.selectbox(
            "Status",
            options=["All", "Success Only", "Failed Only"],
            key="filter_status"
        )

    # Apply filters
    filtered_generations = generations

    if filter_backend and filter_backend != "All Models":
        filtered_generations = [g for g in filtered_generations if g.model_backend == filter_backend]

    if filter_status == "Success Only":
        filtered_generations = [g for g in filtered_generations if g.success]
    elif filter_status == "Failed Only":
        filtered_generations = [g for g in filtered_generations if not g.success]

    st.markdown("---")

    # Display generations
    st.subheader(f"📋 Past Generations ({len(filtered_generations)} shown)")

    for gen in filtered_generations:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 3])

            with col1:
                st.write(f"**ID:** {gen.id}")
                timestamp = gen.created_at.strftime("%Y-%m-%d %H:%M")
                st.write(f"🕐 {timestamp}")

            with col2:
                schema_preview = format_schema_for_display(gen.schema_json)
                if len(schema_preview) > 40:
                    schema_preview = schema_preview[:40] + "..."
                st.write(f"**Schema:** {schema_preview}")
                st.write(f"**Records:** {gen.num_records}")

            with col3:
                # Parse model_backend format: "BackendName:model_id"
                if ":" in gen.model_backend:
                    backend_name, model_id = gen.model_backend.split(":", 1)
                    # Show just the model ID (more useful to user)
                    display_model = model_id
                else:
                    # Fallback for old format
                    display_model = gen.model_backend

                st.write(f"**Model:** {display_model}")
                if gen.success:
                    st.success("✅ Success")
                else:
                    st.error("❌ Failed")

            with col4:
                # Action buttons
                button_col1, button_col2, button_col3 = st.columns(3)

                with button_col1:
                    if st.button("👁️ View", key=f"view_{gen.id}", use_container_width=True):
                        # Load this generation into session state
                        gen_dict = gen.to_dict()
                        st.session_state.generated_data = {
                            'generation_id': gen_dict['id'],
                            'data': gen_dict['data'],
                            'num_records': gen_dict['num_records'],
                            'success': gen_dict['success'],
                            'error_message': gen_dict['error_message'],
                            'raw_response': '',
                            'backend': gen_dict['model_backend']
                        }
                        st.session_state.viewing_historical = True
                        st.session_state.current_generation_id = gen.id
                        st.success("✅ Data loaded! Switch to the 'Generate' tab to view and download.")
                        st.rerun()

                with button_col2:
                    if gen.success and gen.data_json:
                        export_service = ExportService()
                        csv_data = export_service.to_csv(gen.data_json)
                        st.download_button(
                            label="⬇️ CSV",
                            data=csv_data,
                            file_name=f"generation_{gen.id}.csv",
                            mime="text/csv",
                            key=f"download_{gen.id}",
                            use_container_width=True
                        )

                with button_col3:
                    if st.button("🗑️ Delete", key=f"delete_{gen.id}", use_container_width=True):
                        db.delete_generation(gen.id)
                        st.success(f"Deleted generation {gen.id}")
                        st.rerun()

            st.markdown("---")

    db.close()


def main():
    """Main application entry point."""
    init_session_state()

    # Create tabs
    tab1, tab2 = st.tabs(["🎲 Generate", "📜 History"])

    with tab1:
        render_generate_tab()

    with tab2:
        render_history_tab()


if __name__ == "__main__":
    main()
