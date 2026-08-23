# %% [markdown]
# # Exercise - week 2
# 
# ## Prototype of a commercial AI travel brochure generator
# 
# Features:
# - Gradio UI 
# - Streaming
# - Tool integration
# - Model selection

# %%
import os
import base64
from io import BytesIO
from PIL import Image
import gradio as gr
from dotenv import load_dotenv

import openai
from anthropic import Anthropic
import google.generativeai as genai


# %%
# Initialize

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
if anthropic_api_key:
    print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
else:
    print("Anthropic API Key not set")

if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:8]}")
else:
    print("Google API Key not set")

# %%
# Configure the AI clients
openai.api_key = openai_api_key
anthropic_client = Anthropic(api_key=anthropic_api_key)
genai.configure(api_key=google_api_key)

# %%
MODELS = {
    "gpt_model" : "gpt-4o-mini",
    "claude_model" : "claude-3-5-haiku-latest",
    "gemini_model" : "gemini-2.5-flash"}

# %%
# System prompt for travel expert
SYSTEM_PROMPT = """You are an expert travel writer and guide with 20 years of experience. 
You create engaging, informative travel brochures that inspire people to visit destinations.

Your brochures should include:
- A captivating introduction to the city
- Top 5 must-see attractions with brief descriptions
- Local cuisine highlights (2-3 dishes to try)
- Best time to visit
- A practical travel tip
- An inspiring closing statement

Write in an enthusiastic but informative tone. Be specific and include interesting facts.
Keep the total length around 400-500 words."""

# %%
# Tool - get weather

def get_weather_info(city):
    """
    This is our TOOL function. It simulates getting weather information.
    In a real application, you'd call a weather API here.
    """
    # Simulated weather data for demo purposes
    weather_db = {
        "paris": "Mild and pleasant, 15-20°C (59-68°F), occasional rain",
        "tokyo": "Temperate, 10-18°C (50-64°F), cherry blossoms in spring",
        "new york": "Variable, -1-15°C (30-59°F) in winter, 20-29°C (68-84°F) in summer",
        "london": "Cool and rainy, 8-18°C (46-64°F), bring an umbrella",
        "dubai": "Hot and sunny, 25-40°C (77-104°F), very low rainfall",
        "sydney": "Mild to warm, 18-26°C (64-79°F), opposite seasons to Northern Hemisphere",
        "rome": "Mediterranean, 15-30°C (59-86°F), hot and dry in summer",
        "barcelona": "Mediterranean, 13-28°C (55-82°F), pleasant most of year",
    }
    
    city_lower = city.lower()
    for key in weather_db:
        if key in city_lower:
            return weather_db[key]
    
    return "Moderate temperatures year-round, check specific forecasts before travel"

# %%
# Tool definition
tools = [
    {
        "name": "get_weather_info",
        "description": "Gets typical weather information for a city to help travelers plan their visit. Use this when writing about best times to visit or what to pack.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The name of the city to get weather information for"
                }
            },
            "required": ["city"]
        }
    }
]

# %%
# Image generation

def artist(city):
    """
    Generates an image for the city using DALL-E-3
    """
    try:
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"An image representing a vacation in {city}, showing tourist spots and everything unique about {city}, in a vibrant pop-art style",
            size="1024x1024",
            n=1,
            response_format="b64_json",
        )
        image_base64 = image_response.data[0].b64_json
        image_data = base64.b64decode(image_base64)
        return Image.open(BytesIO(image_data))
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# %%
# Text Generation Functions with streaming and weather tool

def generate_with_openai(city, model_name):
    """
    Generates brochure text using OpenAI's GPT models with streaming and weather tool
    """
    try:
        # Define the weather tool
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather_info",
                    "description": "Gets typical weather information for a city to help travelers plan their visit. Use this when writing about best times to visit or what to pack.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "The name of the city to get weather information for"
                            }
                        },
                        "required": ["city"]
                    }
                }
            }
        ]
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Create a travel brochure for {city}. Use the get_weather_info tool to get accurate weather data, then incorporate that specific weather information into your brochure, especially in the 'Best time to visit' section."}
        ]
        
        full_text = ""
        
        # First request - AI might want to call the tool
        response = openai.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=openai_tools,
            tool_choice="required", 
            temperature=0.7,
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # Check if AI wants to use the weather tool
        if tool_calls:
            # If decided to call the tool
            full_text = f"[Using weather tool for {city}...]\n\n"
            yield full_text
            
            # Add AI's response to messages
            messages.append(response_message)
            
            # Execute each tool call
            weather_info_collected = ""
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                import json
                function_args = json.loads(tool_call.function.arguments)
                
                # Call our weather function
                if function_name == "get_weather_info":
                    weather_result = get_weather_info(function_args["city"])
                    weather_info_collected = weather_result  
                    
                    # Add tool result to messages
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": weather_result,
                    })
            
            # Mostrar el clima obtenido
            if weather_info_collected:
                full_text += f"**Weather Data:** {weather_info_collected}\n\n"
                yield full_text
            
            # Añadir un mensaje adicional para asegurar que use la info
            messages.append({
                "role": "user",
                "content": f"Now write the brochure. IMPORTANT: You must include the exact weather information you just retrieved ('{weather_info_collected}') in your 'Best time to visit' section. Don't use generic weather info - use the specific data from the tool."
            })
            
            # Now get the final response with streaming
            stream = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
                temperature=0.7,
            )
            
            # Stream the final response
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_text += content
                    yield full_text
        
        else:
            # AI didn't use the tool, just stream normally
            stream = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True,
                temperature=0.7,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_text += content
                    yield full_text
                    
    except Exception as e:
        yield f"Error with OpenAI: {str(e)}"


def generate_with_claude(city, model_name):
    """
    Generates brochure text using Claude with streaming and weather tool
    """
    try:
        full_text = ""
        
        # request tool access
        with anthropic_client.messages.stream(
            model=model_name,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            tools=tools, 
            messages=[
                {"role": "user", "content": f"Create a travel brochure for {city}. Check the weather information for this city to provide accurate advice."}
            ],
        ) as stream:
            # stream
            for text in stream.text_stream:
                full_text += text
                yield full_text
            
            # Check if wants to use a tool
            final_message = stream.get_final_message()
            
            # If Claude used the weather tool, continue the conversation
            if final_message.stop_reason == "tool_use":
                tool_use_block = None
                for block in final_message.content:
                    if block.type == "tool_use":
                        tool_use_block = block
                        break
                
                if tool_use_block:
                    # Execute the tool
                    tool_name = tool_use_block.name
                    tool_input = tool_use_block.input
                    
                    full_text += f"\n\n[Using tool: {tool_name} for {tool_input['city']}]\n\n"
                    yield full_text
                    
                    # Get weather info
                    weather_result = get_weather_info(tool_input['city'])
                    
                    # Continue the conversation with the tool result
                    with anthropic_client.messages.stream(
                        model=model_name,
                        max_tokens=2000,
                        system=SYSTEM_PROMPT,
                        tools=tools,
                        messages=[
                            {"role": "user", "content": f"Create a travel brochure for {city}. Check the weather information for this city to provide accurate advice."},
                            {"role": "assistant", "content": final_message.content},
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use_block.id,
                                        "content": weather_result,
                                    }
                                ],
                            },
                        ],
                    ) as stream2:
                        for text in stream2.text_stream:
                            full_text += text
                            yield full_text
                            
    except Exception as e:
        yield f"Error with Claude: {str(e)}"


def generate_with_gemini(city, model_name):
    """
    Generates brochure text using Google's Gemini with streaming
    """
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT
        )
        
        # Get weather info and include it in the prompt
        weather = get_weather_info(city)
        prompt = f"""Create a travel brochure for {city}. 

Weather information for {city}: {weather}

Use this weather information to provide helpful advice about the best time to visit."""
        
        # Generate with streaming
        response = model.generate_content(prompt, stream=True)
        
        full_text = ""
        for chunk in response:
            if chunk.text:
                full_text += chunk.text
                yield full_text
                
    except Exception as e:
        yield f"Error with Gemini: {str(e)}"

# %%
# Main Generation Function

def generate_brochure(city, model_choice, include_image):
    """
    Main function that coordinates everything
    This is called when the user clicks the Generate button
    """
    if not city or city.strip() == "":
        yield "Please enter a city name!", None
        return
    
    # Determine which model to use
    if "GPT" in model_choice:
        model_name = MODELS["gpt_model"]
        generator = generate_with_openai(city, model_name)
    elif "Claude" in model_choice:
        model_name = MODELS["claude_model"]
        generator = generate_with_claude(city, model_name)
    else:  # Gemini
        model_name = MODELS["gemini_model"]
        generator = generate_with_gemini(city, model_name)
    
    # Stream the text generation
    for text_chunk in generator:
        yield text_chunk, None
    
    # Generate image if requested
    if include_image:
        yield text_chunk, "Generating image..."
        image = artist(city)
        yield text_chunk, image
    else:
        yield text_chunk, None

# %%
# Create the Gradio Interface

def create_interface():
    """
    Creates the Gradio UI
    """
    with gr.Blocks(title="Travel Brochure Generator", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # AI Travel Brochure Generator
            
            Generate beautiful travel brochures with AI! Choose your destination, 
            select an AI model, and watch as your brochure is created in real-time.
            
            **Features:**
            - Multiple AI models (GPT, Claude, Gemini)
            - AI-generated images with DALL-E-3
            - Real-time streaming
            - Tool use demonstration (Check weather with OpenAI!)
            """
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                # Input controls
                city_input = gr.Textbox(
                    label="City Name",
                    placeholder="e.g., Paris, Tokyo, New York",
                    info="Enter the name of the city you want a brochure for"
                )
                
                model_selector = gr.Radio(
                    choices=["GPT-4o Mini (OpenAI)", 
                             "Claude 3.5 Haiku (Anthropic) - Uses Tools!", 
                             "Gemini 2.0 Flash (Google)"],
                    value="Claude 3.5 Haiku (Anthropic) - Uses Tools!",
                    label="Select AI Model",
                    info="Claude can use the weather tool!"
                )
                
                image_checkbox = gr.Checkbox(
                    label="Generate AI Image",
                    value=True,
                    info="Creates a pop-art style image (costs ~$0.04)"
                )
                
                generate_btn = gr.Button("Generate Brochure", variant="primary", size="lg")
                
            
            with gr.Column(scale=2):
                # Output area
                brochure_output = gr.Textbox(
                    label="Your Travel Brochure",
                    lines=20,
                    max_lines=30,
                    show_copy_button=True
                )
                
                image_output = gr.Image(
                    label="Generated Image",
                    type="pil"
                )
        
        # Connect the generate button to function
        generate_btn.click(
            fn=generate_brochure,
            inputs=[city_input, model_selector, image_checkbox],
            outputs=[brochure_output, image_output]
        )
        
    
    return demo

# Launch app

if __name__ == "__main__":
    print("Starting Travel Brochure Generator...")
    demo = create_interface()
    demo.launch(
        share=False,  
        server_name="127.0.0.1",
        server_port=7860
    )

# %%



