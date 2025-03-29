"""Main application module for CodeXchange AI."""

import logging
import os
from typing import Any, Dict, Generator, Optional, Tuple
import re
from datetime import datetime
import time
import threading

from anthropic import Anthropic, AnthropicError
import google.generativeai as genai
import gradio as gr
from dotenv import load_dotenv
from jinja2 import Template
from openai import OpenAI

# Import configuration
from src.ai_code_converter.config import (
    SUPPORTED_LANGUAGES,
    MODELS,
    LANGUAGE_MAPPING,
    PREDEFINED_SNIPPETS,
    SNIPPET_LANGUAGE_MAP,
    LANGUAGE_FILE_EXTENSIONS
)
from src.ai_code_converter.models.ai_streaming import AIModelStreamer
from src.ai_code_converter.core.code_execution import CodeExecutor
from src.ai_code_converter.core.language_detection import LanguageDetector
from src.ai_code_converter.core.file_utils import FileHandler
from src.ai_code_converter.utils.logger import setup_logger, log_execution_time
from src.ai_code_converter.config import (
    CUSTOM_CSS,
    LANGUAGE_MAPPING,
    MODELS,
    SUPPORTED_LANGUAGES,
    OPENAI_MODEL,
    CLAUDE_MODEL,
    DEEPSEEK_MODEL,
    GEMINI_MODEL,
    GROQ_MODEL
)

# Initialize logger for this module
logger = setup_logger(__name__)

class CodeConverterApp:
    """Main application class for the CodeXchange AI."""
    
    def __init__(self):
        """Initialize the application components."""
        logger.info("Initializing CodeConverterApp")
        try:
            self._setup_environment()
            self._initialize_components()
            self.demo = self._create_gradio_interface()
            logger.info("CodeConverterApp initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize CodeConverterApp", exc_info=True)
            raise
            
    def _load_snippet(self, snippet_name: str) -> Tuple[str, str]:
        """Load a predefined code snippet and get its language
        
        Args:
            snippet_name: Name of the snippet to load
            
        Returns:
            A tuple containing (code_content, language)
        """
        logger.info(f"Loading predefined snippet: {snippet_name}")
        # Use the imported configuration from config.py
        from src.ai_code_converter.config import PREDEFINED_SNIPPETS, SNIPPET_LANGUAGE_MAP
        code = PREDEFINED_SNIPPETS.get(snippet_name, "# No snippet selected")
        language = SNIPPET_LANGUAGE_MAP.get(snippet_name, "Python")
        
        logger.info(f"Snippet loaded with language: {language}")
        return code, language

    def _setup_environment(self) -> None:
        """Set up environment variables and logging."""
        load_dotenv()
        
        # Set up API keys
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')
        os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', 'your-key-if-not-using-env')
        
        # Initialize AI clients
        self.openai = OpenAI()
        self.claude = Anthropic()
        self.deepseek = OpenAI(
            base_url="https://api.deepseek.com/v1",
            api_key=os.getenv('DEEPSEEK_API_KEY', 'your-key-if-not-using-env')
        )
        self.groq = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv('GROQ_API_KEY', 'your-key-if-not-using-env')
        )
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY', 'your-key-if-not-using-env'))
        self.gemini = genai.GenerativeModel('gemini-1.5-flash')

    def _initialize_components(self) -> None:
        """Initialize application components."""
        # Load conversion template using package path
        template_path = os.path.join(os.path.dirname(__file__), 'template.j2')
        with open(template_path, 'r') as f:
            self.template = Template(f.read())
        
        # Initialize components
        self.language_detector = LanguageDetector()
        self.code_executor = CodeExecutor()
        self.file_handler = FileHandler()
        self.model_streamer = AIModelStreamer(
            self.openai,
            self.claude,
            self.deepseek,
            self.groq,
            self.gemini
        )
        
        # Extend Gradio's allowed languages
        for lang in LANGUAGE_MAPPING.values():
            if lang not in gr.Code.languages:
                gr.Code.languages.append(lang)
                
        # Add additional languages to Gradio's supported languages if needed
        additional_languages = {
            "Perl": "perl",
            "Lua": "lua",
            "PHP": "php",
            "Kotlin": "kotlin",
            "SQL": "sql"
        }
        
        for lang, lang_code in additional_languages.items():
            if lang_code not in gr.Code.languages:
                gr.Code.languages.append(lang_code)

    def _create_gradio_interface(self) -> gr.Blocks:
        """Create and configure the Gradio interface."""
        with gr.Blocks(css=CUSTOM_CSS) as demo:
            # Add validation state
            validation_state = gr.State(True)
            error_state = gr.State("")
            
            # Header
            gr.HTML('<div class="header-text">CodeXchange AI</div>')
            
            # Error Message Accordion
            with gr.Accordion("Validation Messages", open=False, elem_classes=["error-accordion"]) as error_accordion:
                error_message = gr.Markdown(
                    value="",
                    elem_classes=["error-message"]
                )
            
            # Code Input/Output
            with gr.Row(equal_height=True):
                with gr.Column(elem_classes="code-container"):
                    source_code = gr.Code(
                        value="",
                        language=LANGUAGE_MAPPING["Python"],
                        label="Source Code",
                        interactive=True,
                        lines=22,
                        elem_classes=["scroll-hide"],
                        container=False
                    )
                with gr.Column(elem_classes="converted-code-container"):
                    converted_code = gr.Code(
                        label="Converted Code",
                        language="python",
                        interactive=False,
                        elem_classes=["code-container"]
                    )
            
            # Language & Model Selection
            with gr.Row():
                source_lang = gr.Dropdown(
                    choices=SUPPORTED_LANGUAGES,
                    value="Python",
                    label="Code In",
                    interactive=True
                )
                target_lang = gr.Dropdown(
                    choices=[lang for lang in SUPPORTED_LANGUAGES if lang != "Python"],
                    value="R",
                    label="Code Out",
                    interactive=True
                )
                model = gr.Dropdown(
                    choices=MODELS,
                    value="GPT",
                    label="Model"
                )
                temperature = gr.Slider(
                    minimum=0,
                    maximum=1,
                    value=0.7,
                    step=0.1,
                    label="Temperature"
                )
            
            # Document Options Row
            with gr.Row(visible=True) as document_row:
                document_checkbox = gr.Checkbox(
                    label="Document",
                    value=True,
                    info="Generate documentation for the converted code"
                )
                
                # Import document styles from config
                from src.ai_code_converter.config import DOCUMENT_STYLES
                
                # Default to R document styles initially
                default_doc_styles = DOCUMENT_STYLES.get("R", [])
                
                # Find the standard style in the choices or use the first one
                default_value = next((item["value"] for item in default_doc_styles if item["value"] == "standard"), 
                                    default_doc_styles[0]["value"] if default_doc_styles else "")
                
                # Convert the styles to the format expected by Gradio
                choices_list = []
                for style in default_doc_styles:
                    choices_list.append(style["label"])
                
                # Map style labels to values for internal use
                self.doc_style_value_map = {style["label"]: style["value"] for style in default_doc_styles}
                
                default_label = next((style["label"] for style in default_doc_styles if style["value"] == default_value), 
                                      default_doc_styles[0]["label"] if default_doc_styles else "Standard")
                
                document_type_dropdown = gr.Dropdown(
                    choices=choices_list,
                    value=default_label,
                    label="Documentation Style",
                    visible=True,
                    interactive=True
                )
            
            # Get default value for document style state
            default_doc_styles = DOCUMENT_STYLES.get("Python", [])
            default_value = next((item["value"] for item in default_doc_styles if item["value"] == "standard"), 
                                default_doc_styles[0]["value"] if default_doc_styles else "")
            
            # Add states to track document options
            document_checkbox_state = gr.State(value=True)
            document_style_state = gr.State(value=default_value)
            
            # File Operations and Code Snippets
            with gr.Accordion("Upload & Code Snippets", open=False, elem_classes="accordion"):
                with gr.Row():
                    file_upload = gr.File(label="Upload File")
                
                with gr.Row():
                    snippet_dropdown = gr.Dropdown(
                        choices=list(PREDEFINED_SNIPPETS.keys()),
                        value=None,
                        label="Example Code Snippets",
                        info="Select a code snippet to load into the editor"
                    )
                    load_snippet_btn = gr.Button(
                        "Load Snippet",
                        variant="secondary",
                        size="sm"
                    )
            
            # Action Buttons
            with gr.Row():
                convert_btn = gr.Button(
                    "Convert Python to R",
                    variant="primary",
                    size="sm"
                )
                clear_btn = gr.Button(
                    "Clear All",
                    variant="stop",
                    size="sm"
                )
            
            # Execution Buttons
            with gr.Row():
                run_source_btn = gr.Button(
                    "Run Python",
                    variant="huggingface",
                    size="sm"
                )
                run_converted_btn = gr.Button(
                    "Run R",
                    variant="huggingface",
                    size="sm"
                )
            
            # Execution Results
            with gr.Row():
                source_result = gr.Code(
                    label="Source Code Result",
                    language=None,
                    interactive=False,
                    lines=5
                )
                converted_result = gr.Code(
                    label="Converted Code Result",
                    language=None,
                    interactive=False,
                    lines=5
                )
            
            # Move Download Buttons into an Accordion
            with gr.Accordion("Download", open=False, elem_classes="accordion"):
                with gr.Row(elem_classes="download-area"):
                    source_download = gr.File(
                        label="Download Source",
                        visible=False
                    )
                    converted_download = gr.File(
                        label="Download Converted",
                        visible=False
                    )
            
            # Set up event handlers
            self._setup_event_handlers(
                source_code, converted_code,
                source_lang, target_lang,
                model, temperature,
                validation_state, error_state,
                error_message, error_accordion,
                file_upload, snippet_dropdown, load_snippet_btn,
                convert_btn, clear_btn,
                run_source_btn, run_converted_btn,
                source_result, converted_result,
                source_download, converted_download,
                document_checkbox, document_type_dropdown, document_checkbox_state, document_style_state
            )
            
            return demo

    def run(self, share: bool = True) -> None:
        """
        Launch the Gradio interface.
        
        Args:
            share: Whether to create a public link
        """
        logger.info("="*50)
        logger.info("Initializing Gradio interface")
        logger.info(f"Supported languages: {SUPPORTED_LANGUAGES}")
        logger.info(f"Available models: {MODELS}")
        
        try:
            self.demo.queue().launch(share=share)
        except Exception as e:
            logger.error(f"Error launching Gradio interface: {str(e)}", exc_info=True)
            raise
        finally:
            logger.info("Gradio interface shutdown")
            logger.info("="*50)

    def _setup_event_handlers(
        self,
        source_code: gr.Code,
        converted_code: gr.Code,
        source_lang: gr.Dropdown,
        target_lang: gr.Dropdown,
        model: gr.Dropdown,
        temperature: gr.Slider,
        validation_state: gr.State,
        error_state: gr.State,
        error_message: gr.Markdown,
        error_accordion: gr.Accordion,
        file_upload: gr.File,
        snippet_dropdown: gr.Dropdown,
        load_snippet_btn: gr.Button,
        convert_btn: gr.Button,
        clear_btn: gr.Button,
        run_source_btn: gr.Button,
        run_converted_btn: gr.Button,
        source_result: gr.Code,
        converted_result: gr.Code,
        source_download: gr.File,
        converted_download: gr.File,
        document_checkbox: gr.Checkbox,
        document_type_dropdown: gr.Dropdown,
        document_checkbox_state: gr.State,
        document_style_state: gr.State
    ) -> None:
        """Set up all event handlers for the Gradio interface."""
        
        # Document checkbox handler
        def _update_document_dropdown_visibility(is_checked: bool) -> tuple[gr.update, bool]:
            """Update document type dropdown visibility based on checkbox state"""
            logger.info(f"Document checkbox changed to: {is_checked}")
            return gr.update(visible=is_checked), is_checked
        
        document_checkbox.change(
            fn=_update_document_dropdown_visibility,
            inputs=[document_checkbox],
            outputs=[document_type_dropdown, document_checkbox_state],
            queue=False
        )
        
        # Language change handlers
        source_lang.change(
            fn=self._handle_source_language_change,
            inputs=[source_code, source_lang, error_state],
            outputs=[source_code, error_message, error_state, error_accordion, validation_state],
            queue=False
        ).then(
            fn=self._update_code_language,
            inputs=[source_lang],
            outputs=[source_code],
            queue=False
        ).then(
            fn=self._update_target_options,
            inputs=[source_lang],
            outputs=[target_lang]
        ).then(
            fn=self._update_button_labels,
            inputs=[source_lang, target_lang],
            outputs=[run_source_btn, run_converted_btn, convert_btn],
            queue=False
        )

        # Code input handlers
        source_code.change(
            fn=self._handle_code_input,
            inputs=[source_code, source_lang, error_state],
            outputs=[source_code, error_message, error_state, error_accordion],
            queue=False
        )

        # File upload handler
        file_upload.change(
            fn=self._handle_file_upload,
            inputs=[file_upload, source_lang, error_state],
            outputs=[source_code, error_message, error_state, error_accordion],
            queue=False
        )

        # Convert button handler
        convert_btn.click(
            fn=self._stream_converted_code,
            inputs=[
                source_code, source_lang, target_lang, model, temperature, validation_state,
                document_checkbox_state, document_type_dropdown
            ],
            outputs=[converted_code, converted_download],
            queue=True,
            show_progress=True
        )

        # Clear button handler
        clear_btn.click(
            fn=self._clear_all,
            outputs=[
                source_code,
                error_message,
                error_state,
                error_accordion,
                converted_code,
                source_result,
                converted_result,
                file_upload
            ],
            queue=False
        )

        # Run code handlers
        run_source_btn.click(
            fn=self._handle_code_execution,
            inputs=[source_code, source_lang],
            outputs=[
                source_result,  # Code component for output
                source_download  # File component for download
            ]
        )

        run_converted_btn.click(
            fn=self._run_converted_code_with_validation,
            inputs=[converted_code, target_lang],
            outputs=converted_result  # Only output string
        )
        
        # Snippet selection handler
        load_snippet_btn.click(
            fn=self._handle_snippet_selection,
            inputs=[snippet_dropdown, error_state],
            outputs=[
                source_code,
                source_lang,
                error_message, 
                error_state, 
                error_accordion, 
                validation_state
            ]
        )

        # Download handlers
        source_code.change(
            fn=self._handle_source_code_change,
            inputs=[source_code, source_lang],
            outputs=[source_download, error_message, error_accordion],
            queue=False
        )
        
        converted_code.change(
            fn=lambda code, lang: self._handle_source_code_change(code, lang),
            inputs=[converted_code, target_lang],
            outputs=[converted_download, error_message, error_accordion],
            queue=False
        )

        # Target language change handler
        target_lang.change(
            fn=self._update_button_labels,
            inputs=[source_lang, target_lang],
            outputs=[run_source_btn, run_converted_btn, convert_btn],
            queue=False
        ).then(
            fn=lambda lang: gr.update(language=LANGUAGE_MAPPING.get(lang, "python")),
            inputs=target_lang,
            outputs=converted_code,
            queue=False
        ).then(
            fn=self._update_document_styles,
            inputs=[target_lang],
            outputs=[document_type_dropdown, document_style_state],
            queue=False
        )

    def _handle_source_language_change(
        self, code: str, new_lang: str, current_error: str
    ) -> tuple[str, str, str, gr.update, bool]:
        """Validate code against newly selected source language."""
        logger.info(f"Verifying code for language change to: {new_lang}")
        
        if not code:
            return "", "", "", gr.update(open=False), True
        
        is_valid, error_msg = self.language_detector.validate_language(code, new_lang)
        if not is_valid:
            logger.warning(f"Language mismatch detected: {error_msg}")
            return (
                code,  # Keep the code but mark as invalid
                f"## ⚠️ Language Mismatch\n{error_msg}",
                error_msg,
                gr.update(open=True),
                False  # Invalid state
            )
        
        logger.info(f"Code verified successfully for {new_lang}")
        return code, "", "", gr.update(open=False), True
        
    def _handle_snippet_selection(
        self, snippet_name: str, current_error: str
    ) -> Tuple[str, str, str, str, gr.update, bool]:
        """Load and validate selected code snippet.
        
        Args:
            snippet_name: Selected snippet name
            current_error: Existing error message
            
        Returns:
            Code, language, error info, and validation status
        """
        logger.info(f"Handling snippet selection: {snippet_name}")
        
        # Default values
        source_code = "# No snippet selected"
        source_lang = "Python"
        error_message = ""
        error_state = ""
        error_accordion_visible = gr.update(open=False)
        is_valid = True
        
        try:
            # Import the configurations from config.py
            from src.ai_code_converter.config import PREDEFINED_SNIPPETS
            
            # Early return if no snippet selected
            if not snippet_name or snippet_name not in PREDEFINED_SNIPPETS:
                logger.warning(f"Invalid snippet name or no snippet selected: {snippet_name}")
                return source_code, source_lang, error_message, error_state, error_accordion_visible, is_valid
            
            # Get code and language from the snippet
            source_code, source_lang = self._load_snippet(snippet_name)
            logger.info(f"Loaded snippet: {snippet_name} with language: {source_lang}")
            
            # Validate that the code matches the language
            if source_code and source_code.strip():
                is_valid, error_details = self.language_detector.validate_language(source_code, source_lang)
                if not is_valid:
                    error_message = f"⚠️ Warning: The code doesn't appear to match {source_lang} syntax perfectly. {error_details}"
                    error_state = error_message
                    error_accordion_visible = gr.update(open=True)
                    logger.warning(f"Snippet validation failed: {error_details}")
        except Exception as e:
            logger.error(f"Error handling snippet selection: {e}", exc_info=True)
            source_code = "# Error loading snippet"
            error_message = f"Error loading snippet: {str(e)}"
            error_state = error_message
            error_accordion_visible = gr.update(open=True)
            is_valid = False
            
        # Return all the updated values in the expected order
        logger.info(f"Returning snippet: Valid={is_valid}, Lang={source_lang}, Error={bool(error_message)}")
        return source_code, source_lang, error_message, error_state, error_accordion_visible, is_valid

    def _update_code_language(self, lang: str) -> gr.update:
        """Set syntax highlighting based on selected language."""
        if not lang:
            return gr.update(language="python")
        
        gradio_lang = LANGUAGE_MAPPING.get(lang, "python").lower()
        logger.info(f"Updating syntax highlighting to: {gradio_lang}")
        
        if gradio_lang not in gr.Code.languages:
            logger.warning(f"Language {gradio_lang} not supported by Gradio, defaulting to python")
            gradio_lang = "python"
        
        return gr.update(language=gradio_lang)

    def _update_target_options(self, source_lang: str) -> gr.update:
        """Filter target language dropdown to exclude source language."""
        if not source_lang:
            return gr.update(choices=SUPPORTED_LANGUAGES)
        available_languages = [lang for lang in SUPPORTED_LANGUAGES if lang != source_lang]
        return gr.update(
            choices=available_languages,
            value=available_languages[0] if available_languages else None
        )

    def _update_button_labels(
        self, source_lang: str, target_lang: str
    ) -> tuple[gr.update, gr.update, gr.update]:
        """Customize button labels with selected language names."""
        source_lang = source_lang or "Python"
        target_lang = target_lang or "Julia"
        
        convert_label = f"Convert {source_lang} to {target_lang}"
        run_source_label = f"Run {source_lang}"
        run_target_label = f"Run {target_lang}"
        
        logger.info(f"Updating button labels: {convert_label}, {run_source_label}, {run_target_label}")
        
        return [
            gr.update(value=run_source_label),
            gr.update(value=run_target_label),
            gr.update(value=convert_label)
        ]
        
    def _update_document_styles(self, target_lang: str) -> tuple[gr.update, str]:
        """Update document style dropdown based on target language.
        
        Args:
            target_lang: Target programming language
            
        Returns:
            Tuple of (dropdown_update, default_style_value)
        """
        from src.ai_code_converter.config import DOCUMENT_STYLES
        
        logger.info(f"Updating document styles for language: {target_lang}")
        
        # Get document styles for the selected language, fallback to empty list
        styles = DOCUMENT_STYLES.get(target_lang, [])
        
        # Default to 'standard' style if available, otherwise use first style in list
        default_style_value = "standard"
        if styles and not any(style.get("value") == "standard" for style in styles):
            default_style_value = styles[0].get("value") if styles else "standard"
        
        # Convert the styles to the format expected by Gradio
        choices_list = [style["label"] for style in styles]
        
        # Update the style label-to-value mapping
        self.doc_style_value_map = {style["label"]: style["value"] for style in styles}
        
        # Get the label corresponding to the default value
        default_label = next((style["label"] for style in styles if style["value"] == default_style_value), 
                            styles[0]["label"] if styles else "Standard")
            
        logger.info(f"Document styles updated: {len(styles)} styles available")
        return gr.update(choices=choices_list, value=default_label), default_style_value

    def _handle_code_input(
        self, code: str, lang_in: str, current_error: str
    ) -> tuple[str, str, str, gr.update]:
        """Handle code input with validation."""
        logger.info(f"Processing code input for {lang_in}")
        
        if not code:
            return "", "", "", gr.update(open=False)
        
        is_valid, error_msg = self.language_detector.validate_language(code, lang_in)
        if not is_valid:
            return code, error_msg, error_msg, gr.update(open=True)
        
        return code, "", "", gr.update(open=False)

    def _handle_file_upload(
        self, file_obj: gr.File, lang_in: str, current_error: str
    ) -> tuple[str, str, str, gr.update]:
        """Handle file upload with validation."""
        logger.info("Processing file upload")
        
        if file_obj is None:
            return "", "", "", gr.update(open=False)
        
        try:
            code = self.file_handler.load_file(file_obj.name)
            is_valid, error_msg = self.language_detector.validate_language(code, lang_in)
            
            if not is_valid:
                return "", f"## ⚠️ Invalid File\n{error_msg}", error_msg, gr.update(open=True)
            
            return code, "", "", gr.update(open=False)
            
        except Exception as e:
            error_msg = f"## ⚠️ Error\nError loading file: {str(e)}"
            logger.error("File upload failed", exc_info=True)
            return "", error_msg, error_msg, gr.update(open=True)

    def _stream_converted_code(
        self,
        code: str,
        lang_in: str,
        lang_out: str,
        model: str,
        temperature: float,
        is_valid: bool,
        document_enabled: bool = True,
        document_style: str = "Standard"
    ) -> tuple[gr.update, gr.update]:
        """Stream the converted code with syntax highlighting."""
        response = self._convert_code(
            code, lang_in, lang_out, model, temperature,
            document_enabled=document_enabled, document_style=document_style
        )
        
        if not response:
            return gr.update(value="", visible=True), gr.update(visible=False)
        
        target_lang = LANGUAGE_MAPPING.get(lang_out, "python").lower()
        
        # Prepare download if conversion was successful
        temp_file, filename = self.file_handler.prepare_download(response, lang_out)
        if temp_file and filename:
            return (
                gr.update(value=response, language=target_lang, visible=True),
                gr.update(value=temp_file, visible=True, label=f"Download {lang_out} Code")
            )
        
        return gr.update(value=response, language=target_lang, visible=True), gr.update(visible=False)

    def _clear_all(self) -> tuple:
        """Clear all fields while retaining language settings."""
        return (
            gr.update(value=""),  # source_code
            "",  # error_message
            "",  # error_state
            gr.update(open=False),  # error_accordion
            gr.update(value=""),  # converted_code
            gr.update(value=""),  # source_result
            gr.update(value=""),  # converted_result
            None  # file_upload
        )

    def _handle_code_execution(self, code: str, language: str) -> tuple[str, gr.update]:
        """Handle code execution and prepare download."""
        if not code:
            return "", gr.update(visible=False)
        
        try:
            # Execute code and get output and binary
            output, binary = self.code_executor.execute(code, language)
            
            # Prepare download with compiled binary if available
            if binary and language in ["C++", "Java", "Go"]:
                # Ensure binary is bytes
                binary_data = binary if isinstance(binary, bytes) else None
                if binary_data:
                    logger.info(f"Got compiled binary for {language}, size: {len(binary_data)} bytes")
                else:
                    logger.warning(f"No valid binary data for {language}")
                    
                temp_file, filename = self.file_handler.prepare_download(
                    code=code,
                    language=language,
                    compiled_code=binary_data
                )
                
                if temp_file and filename:
                    return (
                        output,  # Return just the output string for Code component
                        gr.update(value=temp_file, visible=True, label=f"Download {language} Code")
                    )
            
            return output, gr.update(visible=False)
            
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}", exc_info=True)
            return f"Error: {str(e)}", gr.update(visible=False)

    def _run_converted_code_with_validation(self, code: str, target_lang: str) -> str:
        """Validate and execute converted code."""
        logger.info(f"Validating converted code for execution")
        
        if not code:
            return "No code to execute."
        
        is_valid, error_msg = self.language_detector.validate_language(code, target_lang)
        if not is_valid:
            logger.error(f"Language validation failed: {error_msg}")
            return f"⚠️ Error: Cannot execute code.\n{error_msg}"
        
        logger.info("Language validation passed, proceeding with execution")
        # Only return the output string, ignore binary
        output, _ = self.code_executor.execute(code, target_lang)
        return output

    def _handle_source_code_change(
        self, code: str, lang: str
    ) -> tuple[gr.update, str, gr.update]:
        """Handle source code changes with validation."""
        if not code:
            return gr.update(visible=False), "", gr.update(open=False)
        
        try:
            temp_file, filename = self.file_handler.prepare_download(code, lang)
            if temp_file and filename:
                return (
                    gr.update(value=temp_file, visible=True, label=f"Download {lang} Code"),
                    "",
                    gr.update(open=False)
                )
            else:
                return (
                    gr.update(visible=False),
                    "## ⚠️ Error preparing download",
                    gr.update(open=True)
                )
        except Exception as e:
            logger.error(f"Error preparing download: {str(e)}", exc_info=True)
            return (
                gr.update(visible=False),
                f"## ⚠️ Error preparing download: {str(e)}",
                gr.update(open=True)
            )

    @log_execution_time(logger)
    def _convert_code(self, code: str, lang_in: str, lang_out: str, model: str, temp: float, document_enabled: bool = True, document_style: str = "Standard") -> str:
        """Convert code between programming languages.
        
        Args:
            code: Source code to convert
            lang_in: Source language
            lang_out: Target language
            model: LLM model to use
            temp: Temperature parameter
            document_enabled: Whether to include documentation
            document_style: Documentation style to apply
            
        Returns:
            Converted code string
        """
        logger.info("STARTING CODE CONVERSION")
        logger.info(f"Params: {lang_in} → {lang_out} | Model: {model} | Temp: {temp}")
        logger.info(f"Documentation: {document_enabled}, Style: {document_style}")
        
        # Log input parameters (excluding sensitive data)
        logger.debug({
            "source_language": lang_in,
            "target_language": lang_out,
            "model": model,
            "temperature": temp,
            "code_length": len(code),
            "process_id": os.getpid(),
            "thread_id": threading.get_ident()
        })
        
        # Parameter validation
        if not all([code, lang_in, lang_out, model]):
            missing = [param for param, value in {
                'code': code,
                'source_language': lang_in,
                'target_language': lang_out,
                'model': model
            }.items() if not value]
            logger.warning("Missing required parameters", extra={
                "missing_params": missing
            })
            return ""
            
        try:
            # Code validation
            validation_start = time.time()
            logger.info("Starting code validation")
            is_valid, message = self.language_detector.validate_language(code, lang_in)
            logger.debug(
                "Validation completed in %.4fs",
                time.time() - validation_start
            )
            
            if not is_valid:
                logger.error("Code validation failed", extra={
                    "error_message": message,
                    "source_language": lang_in
                })
                return message
                
            logger.info("Code validation successful")
            
            # Create and execute prompt
            prompt_start = time.time()
            
            # Map the document style label to its value
            style_value = "standard"  # Default fallback
            if document_style in self.doc_style_value_map:
                style_value = self.doc_style_value_map[document_style]
            else:
                logger.warning(f"Document style mapping not found for '{document_style}', using 'standard' as fallback")
            
            prompt = self.template.render(
                source_language=lang_in,
                target_language=lang_out,
                input_code=code,
                doc_enabled=document_enabled,
                doc_style=style_value
            )
            logger.debug(
                "Prompt creation completed in %.4fs",
                time.time() - prompt_start
            )
            
            logger.info(f"Template: doc_enabled={document_enabled}, style={style_value} (from {document_style})")
            
            # Stream model response
            stream_start = time.time()
            logger.info(f"Starting {model} stream")
            progress = gr.Progress(track_tqdm=True)
            
            response = self._stream_model_response(model, prompt, progress)
            logger.debug(
                "Streaming completed in %.4fs",
                time.time() - stream_start
            )
            
            # Clean response
            clean_start = time.time()
            cleaned_response = self._clean_response(response)
            logger.debug(
                "Response cleaning completed in %.4fs",
                time.time() - clean_start
            )
            
            # If converting to Python, ensure output is visible
            if lang_out == "Python":
                cleaned_response = self._prepare_python_code(cleaned_response)
            
            logger.info("Code conversion completed successfully", extra={
                "output_length": len(cleaned_response)
            })
            logger.info("="*50)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(
                "Error during code conversion",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "source_language": lang_in,
                    "target_language": lang_out,
                    "model": model
                }
            )
            logger.info("="*50)
            return f"Error during conversion: {str(e)}"

    def _stream_model_response(self, model: str, prompt: str, progress: gr.Progress) -> str:
        """Stream response from selected model with logging."""
        logger = logging.getLogger(__name__)
        
        logger.info(f"Streaming response from {model}")
        response = ""
        
        try:
            if model == "GPT":
                stream = self.model_streamer.stream_gpt(prompt)
            elif model == "Claude":
                stream = self.model_streamer.stream_claude(prompt)
            elif model == "DeepSeek":
                stream = self.model_streamer.stream_deepseek(prompt)
            elif model == "GROQ":
                stream = self.model_streamer.stream_groq(prompt)
            elif model == "Gemini":
                stream = self.model_streamer.stream_gemini(prompt)
            else:
                logger.error(f"Unsupported model selected: {model}")
                return "Unsupported model selected"
            
            for i, chunk in enumerate(stream):
                response = chunk
                progress_value = min(0.99, (1 - (1 / (1 + 0.1 * i))))
                progress(progress_value, desc=f"Converting - {int(progress_value * 100)}%")
                
            logger.info(f"Streaming completed for {model}")
            return response
            
        except Exception as e:
            logger.error(f"Error streaming from {model}", exc_info=True)
            raise

    def _clean_response(self, response: str) -> str:
        """Clean up the model response."""
        try:
            cleaned = re.sub(
                r'(```\w*\n?)|(^Here is the converted( is the converted)?.*?\n)',
                '',
                response,
                flags=re.MULTILINE
            )
            return cleaned.strip()
        except Exception as e:
            logger.error(f"Error cleaning response: {str(e)}", exc_info=True)
            return response

    def _prepare_python_code(self, code: str) -> str:
        """Prepare Python code for execution by ensuring output is visible."""
        # Split code into lines
        lines = code.strip().split('\n')
        
        # Track function definitions and their indentation
        functions = {}
        modified_lines = []
        current_function = None
        in_function = False
        
        for line in lines:
            stripped = line.strip()
            
            # Handle function definitions
            if stripped.startswith('def '):
                current_function = stripped[4:].split('(')[0].strip()
                in_function = True
                functions[current_function] = True
                modified_lines.append(line)
                continue
            
            # Check if we're still in a function definition
            if in_function:
                if line and line[0].isspace():
                    modified_lines.append(line)
                    continue
                else:
                    in_function = False
                    current_function = None
            
            # Skip imports, comments, and empty lines
            if not stripped or stripped.startswith(('import ', 'from ', '#')):
                modified_lines.append(line)
                continue
            
            # Handle function calls and other statements
            if not in_function and stripped:
                # Don't wrap lines that already have print
                if stripped.startswith('print('):
                    modified_lines.append(line)
                # Don't wrap function definitions or control flow statements
                elif any(stripped.startswith(keyword) for keyword in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except:', 'finally:', 'else:', 'elif ']):
                    modified_lines.append(line)
                # Don't wrap assignments
                elif '=' in stripped and not stripped.startswith('return'):
                    modified_lines.append(line)
                # Wrap function calls and expressions
                else:
                    modified_lines.append(f"print({stripped})")
        
        # Add a final newline for cleaner output
        return '\n'.join(modified_lines) + '\n' 