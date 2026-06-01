"""A chabot interface the supports question answering and tool calls with streaming. It also supports image generation as a tool call. 
This assumes use of the XAI API, but can be modified to work with other APIs. 

All generated images are written to disk. The default path is c:\temp, but can be changed by modifying the call to ModelContext.create in the __main__ block.
"""
from PIL import Image
import base64
from contextlib import contextmanager
import inspect
import os
import json
import re
from typing import Any, Callable, Generator, Optional, cast
import uuid
from attr import dataclass
from dotenv import load_dotenv
from openai import OpenAI, Stream, omit
from openai.types.chat import ChatCompletionChunk
import gradio as gr
from datetime import datetime
from types import SimpleNamespace
import io

def today_date():
    """Tool function to return today's date"""
    return datetime.now().strftime("%Y-%m-%d")

@dataclass
class ToolResult:
    content_for_model: str
    content:Any
    content_type:str = "text"

    def __str__(self) -> str:
        # Convert content to string and slice first 100 characters
        content_str = str(self.content)
        truncated = content_str[:100] + "..." if len(content_str) > 100 else content_str
        
        return (
            f"ToolResult:\n"
            f"  Model Content: {self.content_for_model}\n"
            f"  Type: {self.content_type}\n"
            f"  Content Preview: {truncated}"
        )

    def __repr__(self) -> str:
        # Convert content to string, slice first 100 characters, and keep it safe for a single line
        content_str = str(self.content)
        truncated = content_str[:100] + "..." if len(content_str) > 100 else content_str
        
        return (
            f"ToolResult(content_for_model={self.content_for_model!r}, "
            f"content_type={self.content_type!r}, "
            f"content_preview={truncated!r})"
        )

class Models:
    IMAGES = "grok-imagine-image"
    QUESTIONS = "grok-4-1-fast-reasoning"
    COMPLEX_QUESTIONS = "grok-4.3"

class ModelContext:
    _instance:Optional["ModelContext"] = None

    def __init__(self, client:OpenAI, image_path:str):
        self.model_name = Models.QUESTIONS
        self._client = client
        self._image_path = image_path
        self._tools = Tools()

    @classmethod
    def create(cls, client:OpenAI, image_path:str):
        """Initialize or return the singleton ModelContext instance.

        Args:
            client (OpenAI): The OpenAI client instance used for API calls.
            image_path (str): Directory path where generated images will be saved.

        Returns:
            ModelContext: The singleton ModelContext instance.
        """
        if cls._instance is None:
            cls._instance = cls(client, image_path)
        return cls._instance
    
    @classmethod
    def current(cls):
        """Return the currently initialized ModelContext instance.

        Raises:
            Exception: If the ModelContext has not been initialized.

        Returns:
            ModelContext: The current ModelContext instance.
        """
        if cls._instance:
            return cls._instance
        
        raise Exception("ModelContext has not been initialized. Call ModelContext.create(client, image_path) first.")

    @property
    def model_name(self)->str:
        """Get the name of the current model in use."""
        return self._model_name

    @model_name.setter
    def model_name(self, value:str):
        """Set the current model name."""
        self._validate_model(value)
        self._model_name = value
    
    def _validate_model(self, model_name:str):
        if model_name not in [Models.IMAGES, Models.QUESTIONS, Models.COMPLEX_QUESTIONS]:
            raise ValueError(f"Invalid model name: {model_name}")
        
    @property
    def client(self)->OpenAI:
        """Get the OpenAI client used by this context."""
        return self._client
    
    @property
    def image_path(self)->str:
        """Get the directory path where generated images are stored."""
        return self._image_path
    
    @property
    def tools(self)->"Tools":
        """Get the registered tool manager."""
        return self._tools
    
    def register_tool(self, func:Callable, description:str):
        """Register a callable as a tool for the LLM to use."""
        self._tools.register_tool(func, description)

    def remove_tool(self, func:Callable):
        """Remove a registered tool from the tool registry."""
        self._tools.remove_tool(func)

    def handle_tool_calls(self, message)->tuple[list[dict[str, Any]], list[ToolResult|None]]:
        """Execute tool calls requested by the model and return their responses."""
        return self._tools.handle_tool_calls(message)
    
    def get_tools_for_model(self) -> list[dict[str, Any]]:
        """Return the tool metadata formatted for model use."""
        return self._tools.get_tools_for_model()
    
    @contextmanager
    def use_model(self, model_name:str):
        """Temporarily switch the current model within a context block."""
        self._validate_model(model_name)
        old_model = self.model_name
        self.model_name = model_name
        try:
            yield
        finally:
            self.model_name = old_model

class Tools:
    def __init__(self):
        """Initialize the tool registry."""
        self.tools = {}

    def register_tool(self, func:Callable, description:str):
        """Register a function as a tool that the model can call.

        Parameter types are derived from function annotations, and descriptions are derived from the function docstrings.

        Args:
            func (Callable): The function to register as a tool.
            description (str): A brief description of what the tool does.
        """
        parameters = {}
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            parameters[param_name] = {"type": get_property_type(param.annotation, True), "description": get_description(func.__doc__, param_name)}
        self.tools[func.__name__] = {"function": func,
                            "json": {
                                "name": func.__name__,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": parameters,
                    },
                    "required": [
                        name for name, param in sig.parameters.items()
                        if param.default is inspect.Parameter.empty 
                        and param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                    ],
                    "additional_properties": False,
                    }
                }

    def remove_tool(self, func:Callable):
        """Removes a tool from the registry."""
        if func.__name__ in self.tools:
            del self.tools[func.__name__]

    def handle_tool_calls(self, message)->tuple[list[dict[str, Any]], list[ToolResult|None]]:
        """Handles tool calls from the model by executing the corresponding functions and returning their results."""
        responses = []
        tool_results:list[ToolResult|None] = []
        for tool_call in message.tool_calls:
            print(f"Got tool call {tool_call}")
            func = self.tools.get(tool_call.function.name, {})
            if func:
                try:
                    arguments = json.loads(tool_call.function.arguments)
                    print(f"Calling function {func['function']} with arguments {arguments}")
                    result = func['function'](**arguments)
                    print(f"Got result {result} from tool call")
                    
                    result_for_model = result
                    if isinstance(result, ToolResult):
                        result_for_model = result.content_for_model
                        tool_results.append(result)
                    else:
                        tool_results.append(None)

                    responses.append({
                        "role": "tool",
                        "content": result_for_model or "",
                        "tool_call_id": tool_call.id
                    })
                except Exception as e:
                    print(f"Error executing tool {tool_call.function.name}: {e}")
                    arguments = {}
                    responses.append({
                        "role": "tool",
                        "content": f"Error executing tool {tool_call.function.name}",
                        "tool_call_id": tool_call.id
                    })

                
        return responses, tool_results

    def get_tools_for_model(self) -> list[dict[str, Any]]:
        """Return the tool metadata formatted for the model's tool interface."""
        return [{"type": "function", "function": self.tools[t]["json"]} for t in self.tools]    

def init_api(api_key_name:str, api_url:str)->OpenAI:
    """Initialize the OpenAI client using environment configuration.

    Args:
        api_key_name (str): Environment variable name for the API key.
        api_url (str): Base URL for the OpenAI-compatible API.

    Returns:
        OpenAI: Configured OpenAI client instance.
    """
    load_dotenv()
    api_key = os.getenv(api_key_name)
    return OpenAI(api_key=api_key, base_url=api_url)


def get_property_type(annotation, for_xai: bool):
    """Return the JSON property type name for a function annotation."""
    if for_xai:
        if annotation == str or annotation == inspect.Parameter.empty:
            return "string"
    return annotation.__name__ if annotation != inspect.Parameter.empty else "str"


def get_description(docstring, param_name):
    """Extract a parameter description from a function docstring.

    Args:
        docstring (str): The function docstring to parse.
        param_name (str): The parameter name to locate.

    Returns:
        str: The description text for the parameter, or an empty string if none found.
    """
    if not docstring:
        return ""
    lines = docstring.splitlines()
    for line in lines:
        line = line.strip()
        if param_name in line and ':' in line:
            return line.partition(':')[2].strip()
    return ""


class ChatInterface:
    SYSTEM_MESSAGE = "You are a helpful assistant. Only answer factually, and if you do not know the answer don't make anything up."
    
    def __init__(self, modelContext:ModelContext):
        """Create a chat interface that streams responses and manages tool usage.

        Args:
            modelContext (ModelContext): The shared model context used for API calls and tools.
        """
        self.chat_history: list[dict[str, str]] = []
        self.modelContext = modelContext
        self.image:Optional[Image.Image] = None
        
    def _get_model_for_choice(self, choice: str) -> str:
        """Map dropdown choice to appropriate model."""
        if choice == "Question":
            return Models.QUESTIONS
        elif choice == "Complex Question":
            return Models.COMPLEX_QUESTIONS
        elif choice == "Generate Image":
            return Models.QUESTIONS
        return Models.QUESTIONS
    
    def _get_system_message_for_choice(self, choice:str)->str:
        """Get system message based on choice."""
        if choice == "Generate Image":
            return """You are an assistant that helps generate images based on user requests.
             The user will provide a description of the image they want and you will help them refine that description if needed, and then call the image generation tool with the final prompt.
             Call the image generation tool at most once per user request. If the request violates the content guidelines, do not call the tool at all; instead refuse the request and explain which part violates the guidelines.
             Do not issue multiple image generation tool calls for the same request.
             Always follow the content guidelines for image generation: the user must not ask for an image that contains nudity, suggestive content, or graphic violence. However, acts of affection (e.g. hugging, kissing), display of weapons (e.g. swords, guns, knives), preparation for warfare (e.g. building fortifications, assembling troops) are acceptable.
             If the user asks for an image but does not provide enough details, ask them for more information and suggest additional details.
             Only tell the user that you are calling the image generation tool when you are actually making a tool call. If the prompt that you pass to the tool is different from the user's original prompt, include the final prompt in your message to the user.

             Examples:
                User: I want a picture of a dog.
                Assistant: Can you provide more details about the dog picture you want? For example, what breed of dog, what setting or background, any specific colors or actions you want the dog to be doing?

                User: I would like a picture of a man with dark hair and skin wearing armor and holding a sword in an outstretched hand. The man is standing on a desolate battlefield with smoke in the background.
                Assistant: Calling the image generation tool.
                Tool Call: Generated Image

                User: I want a picture of a man with his head cut off.
                Assistant: I'm sorry, but I cannot generate that image because it violates the content guidelines regarding graphic violence. Specifically, the request for a picture of a man with his head cut off is not something I can assist with. Please let me know if you have another image request that follows the guidelines.

                User: I want a picture of a woman in a bikini.
                Assistant: I'm sorry, but I cannot generate that image because it violates the content guidelines regarding suggestive content. Specifically, the request for a picture of a woman in a bikini is not something I can assist with. Please let me know if you have another image request that follows the guidelines.
             """
        return self.SYSTEM_MESSAGE
    
    def _collect_stream(self, stream:Stream[ChatCompletionChunk])->Generator[tuple[str, Any], None, None]:
        """Collect all chunks from a stream, yielding text content and accumulating tool calls."""
        full_content = ""
        tool_calls_by_index: dict[int, dict[str, Any]] = {}

        for chunk in stream:
            choice = chunk.choices[0]
            delta = choice.delta

            if delta.content:
                token = delta.content
                full_content += token
                yield ("text", token)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = getattr(tc, "index", 0) or 0
                    if idx not in tool_calls_by_index:
                        tool_calls_by_index[idx] = {
                            "id": "",
                            "function": {"name": "", "arguments": ""},
                        }
                    acc = tool_calls_by_index[idx]
                    if getattr(tc, "id", None) is not None:
                        acc["id"] = tc.id
                    if getattr(tc, "function", None) is not None:
                        if getattr(tc.function, "name", None) is not None:
                            acc["function"]["name"] = tc.function.name #type: ignore[union-attr]
                        if getattr(tc.function, "arguments", None) is not None:
                            acc["function"]["arguments"] += tc.function.arguments or "" #type: ignore[union-attr]

            if getattr(choice, "finish_reason", None) == "tool_calls" and tool_calls_by_index:
                tool_message = SimpleNamespace(tool_calls=[])
                for tool_call_info in tool_calls_by_index.values():
                    function = SimpleNamespace(
                        name=tool_call_info["function"]["name"],
                        arguments=tool_call_info["function"]["arguments"],
                    )
                    tool_message.tool_calls.append(
                        SimpleNamespace(
                            id=tool_call_info["id"],
                            function=function,
                        )
                    )
                tool_calls_by_index.clear()

                tool_responses, tool_results = self.modelContext.handle_tool_calls(tool_message)
                yield ("tool_call", tool_responses)
                yield ("tool_result", tool_results)
    
    def chat(self, message: str, chat_history: list[dict[str, str]], choice: str)->Generator[Any, Any, Any]:
        """Stream chat responses token by token and handle tool calls.

        Args:
            message (str): The user's input message.
            chat_history (list[dict[str, str]]): Current chat history from the UI.
            choice (str): Selected chat mode, such as question or image generation.

        Yields:
            tuple: Intermediate chat history and optional image data while streaming.
        """
        if not message:
            return chat_history, self.image
        
        # Add user message to history
        self.chat_history.append({"role": "user", "content": message})
        local_chat_history = [c for c in self.chat_history]  # Create a local copy for this interaction
        yield local_chat_history + [{"role": "assistant", "content": "",  "metadata": {"title": "Thinking...", "status": "pending"}}], self.image  # Yield initial state with user message added
        
        model = self._get_model_for_choice(choice)
        is_image_mode = choice == "Generate Image"

        
        try:
            # Process in a loop to handle tool calls and follow-ups
            while True:
                # Build messages with system context
                messages = [{"role": "system", "content": self._get_system_message_for_choice(choice)}]
                messages.extend(self.chat_history)
                
                # Create streaming response
                # prevent the model from calling the image generation tool multiple times for a single response.
                stream = self.modelContext.client.chat.completions.create(
                    model=model,
                    messages=messages, # type:ignore[arg-type]
                    tools=self.modelContext.get_tools_for_model(), #type:ignore[arg-type]
                    stream=True,
                )
                
                # Collect and stream all chunks
                full_response = ""    
                tool_calls = []        
                for item_type, tool_results in self._collect_stream(cast(Stream[ChatCompletionChunk], stream)):
                    if item_type == "text":
                        full_response += tool_results
                        yield local_chat_history + [{"role": "assistant", "content": full_response or ""}], self.image
                    elif item_type == "tool_call":
                        tool_calls.extend(tool_results)
                    elif item_type == "tool_result" and is_image_mode:
                        for image_data in [i.content for i in tool_results if i and i.content_type == "image"]:
                            self.image = Image.open(io.BytesIO(image_data))
                            yield local_chat_history + [{"role": "assistant", "content": full_response or ""}], self.image
                
                # Add assistant response to history
                if full_response:
                    history_entry = {"role": "assistant", "content": full_response or ""}
                    self.chat_history.append(history_entry)
                    local_chat_history.append(history_entry)
                if tool_calls:
                    self.chat_history.extend(tool_calls)
                    local_chat_history.extend(tool_calls)
                    if is_image_mode and self.image:
                        # make sure no additonal images are generated for the same prompt.
                        self._print_chat()
                        break
                    
                    continue
                
                self._print_chat()
                break
                
        except Exception as e:
            print(f"Error in chat: {e}")
            # Show generic error without details
            error_msg = "I encountered an error processing your request. Please try again."
            self.chat_history.append({"role": "assistant", "content": error_msg})
            yield self.chat_history, self.image

    def _print_chat(self):
        print("*********** Finished a chat iteration ***********")
        for entry in self.chat_history:
            print(entry)
        print("**********************************************")
    
    def clear_history(self):
        """Clear stored chat history and reset the image output."""
        self.chat_history = []
        self.image = None
        return []


def launch_app():
    """Launch the Gradio Blocks interface."""
    chat_interface = ChatInterface(ModelContext.current())
    
    with gr.Blocks(title="AI Assistant") as demo:
        gr.Markdown("# AI Assistant")
        
        with gr.Row():
            choice = gr.Dropdown(
                choices=["Question", "Complex Question", "Generate Image"],
                value="Question",
                label="Select Mode",
                interactive=True
            )
        
        chatbot = gr.Chatbot(
            label="Chat",
            type="messages",
            height=400
        )
        
        image_output = gr.Image(
            label="Generated Image",
            visible=False,
            type="pil"
        )
        
        with gr.Row():
            message_input = gr.Textbox(
                label="Message",
                placeholder="Type your message here...",
            )
        
        with gr.Row():
            submit_btn = gr.Button("Submit", variant="primary")
            clear_btn = gr.Button("Clear")
        
        def on_choice_change(selected_choice):
            """Update image visibility based on choice."""
            if selected_choice == "Generate Image":
                ModelContext.current().register_tool(generate_image_tool, "Generate an image based on a text prompt")
            else:
                ModelContext.current().remove_tool(generate_image_tool)

            return gr.update(visible=(selected_choice == "Generate Image"))
        
        choice.change(
            fn=on_choice_change,
            inputs=choice,
            outputs=image_output
        )
        
        def handle_submit(message, chat_history, selected_choice):
            """Handle message submission."""
            if not message:
                return chat_history, "", None
            
            for updated_history, image_data in chat_interface.chat(message, chat_history, selected_choice):
                yield updated_history, "", image_data
        
        def handle_clear():
            """Handle clear button."""
            cleared_history = chat_interface.clear_history()
            return cleared_history, "", None
        
        submit_event = {"fn": handle_submit,
            "inputs": [message_input, chatbot, choice],
            "outputs": [chatbot, message_input, image_output]}
        
        # Submit on button click
        submit_btn.click(
            **submit_event
        )
        
        # Submit on Enter key (textbox submission)
        message_input.submit(**submit_event)
        
        
        # Clear button
        clear_btn.click(
            fn=handle_clear,
            outputs=[chatbot, message_input, image_output]
        )
    
    return demo

def generate_image(prompt:str, model:str, client:OpenAI, image_path:str)->tuple[str, bytes]:
    """Example function to generate an image using the API."""
    image_system_prompt = "Generate an image based on the request below. The generaged image must not include any nudity, suggestive content, or graphic violence. If requested, acts of affection (e.g. hugging, kissing) and display of weapons (e.g swords, guns, knives) is acceptable. If the requested picture does not meet the guidelines generate a picture of a peaceful landscape instead. Always follow the guidelines and never generate content that violates them.\n\nRequest:"
    image_response = client.images.generate(
            model=model,
            prompt=f"{image_system_prompt}\n\n{prompt}",
            size=omit,
            n=1,
            response_format="b64_json",
        )
    image_base64 = image_response.data[0].b64_json # type: ignore[index]
    image_data = base64.b64decode(image_base64) # type:ignore[arg-type]
    image_file = os.path.join(image_path, f"{uuid.uuid4()}.png")
    with open(image_file, "wb") as f:
        f.write(image_data)
    
    print(f"Generated image saved to {image_file}")

    return (image_file, image_data)

def generate_image_tool(prompt:str)->ToolResult:
    """Tool function to generate an image."""
    model_context = ModelContext.current()
    with model_context.use_model(Models.IMAGES):
        _, image_data = generate_image(prompt, model_context.model_name, model_context.client, model_context.image_path)
    # uncomment below to test with a static image instead of generating a new one each time.
    # with open(r"C:\Users\jordan-dev\model_output\images\5e6305fa-e54d-496b-b742-6f49ba5f1e45.png", "rb") as f:
    #     image_data = f.read()

    return ToolResult(content_for_model="Generated an image.", content=image_data, content_type="image")


if __name__ == "__main__":
    load_dotenv()
    xai_api_key = os.getenv('XAI_API_KEY')
    client = init_api("XAI_API_KEY", "https://api.x.ai/v1")
    ModelContext.create(client, r"C:\temp")
    ModelContext.current().register_tool(today_date, "Get today's date in YYYY-MM-DD format")
    app = launch_app()
    app.launch()