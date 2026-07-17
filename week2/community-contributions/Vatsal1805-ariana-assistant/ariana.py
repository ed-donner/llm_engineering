
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import requests
import gradio as gr
from bs4 import BeautifulSoup

def fetch_website_contents(url:str) ->str:
    """ Fetch a webpage and return clean readable text."""
    
    try:
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }
        response=requests.get(url,headers=headers,timeout=30)
        response.raise_for_status()
        
        soup=BeautifulSoup(response.content,"html.parser")
        
        for tag in soup(["script","style","nav","footer","header","aside","form"]):
            tag.decompose()
            
        text=soup.get_text(separator="\n",strip=True)

        lines=[line.strip() for line in text.splitlines() if line.strip()]
        clean_text="\n".join(lines)
        
        return clean_text[:8000]
    except Exception as e:
        return f"⚠️ Could not fetch URL: {e}"
    
    
load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite"
OLLAMA_MODEL = "llama3.2"

gemini=OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

ollama=OpenAI(
    api_key="ollama",
    base_url="http://localhost:11434/v1"
)

if GEMINI_API_KEY:
    print(" gemini key loaded successfully!")
else:
    print("GEMINI_API_KEY not found in .env file!")
    print("   Go to https://aistudio.google.com/app/apikey and get a free key")

def get_client_and_model(model_choice: str):
    """
    Returns the right Ai cleint and model name based on dropdown choice.
    """
    if "Gemini" in model_choice:
        return gemini,GEMINI_MODEL
    elif "Llama" in model_choice or "Ollama" in model_choice:
        return ollama, OLLAMA_MODEL
    else:
        return gemini,GEMINI_MODEL
    
CHAT_SYSTEM_PROMPT = """
You are ARIA (AI Research & Information Assistant), a friendly and knowledgeable AI.
Your goal is to help users understand content, answer questions, and research topics.

Your style:
- Be clear, concise, and friendly, humorously balancing professionalism and fun.
- Use markdown formatting (bold, bullet points, headers) for clarity.
- When you don't know something, use your search tools.
- Always be honest — admit uncertainty.

Your capabilities:
- Summarize and explain articles and web pages.
- Answer questions using Wikipedia (use the tool!).
- Check weather for any city (use the tool!).
- Discuss any topic the user has loaded.

CRITICAL RULES:
- Do NOT use tools for simple greetings, hello, hi, or casual chit-chat. Respond directly without calling any tools for greetings.
- Only use tools when explicitly asked for facts, weather, time, or information not present in the context.
"""

# This is used when summarizing a URL in the SUMMARIZE tab
SUMMARY_SYSTEM_PROMPT = """
You are an expert content summarizer. Create a well-structured, clear summary.

Format your response with:
- **Bold** for important terms
- ## for section headers
- Bullet points for lists or key points
- A "## 🔑 Key Takeaways" section at the end

Be thorough but concise. Focus on what's most valuable for the reader.
Respond in clean markdown without wrapping it in a code block.
"""


def search_wikipedia(query: str)-> str:
    """ Search Wikipedia for any topic. Free-no api  key needed."""
    print(f"\n [tool called] wikepedia search")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        response = requests.get(url,headers=headers, timeout=20)
        if response.status_code==200:
            data=response.json()
            title=data.get("title","")
            extract=data.get("extract","")
            wiki_url=data.get("content_urls",{}).get("desktop",{}).get("page","")
            return f"**{title}** (Wikipedia)\n\n{extract}\n\nSource: {wiki_url}"
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1
        }
        search_resp = requests.get(search_url, params=params,headers=headers, timeout=10)
        results = search_resp.json().get("query", {}).get("search", [])
        
        if results:
            top=results[0]
            return f" **{top['title']}** (Wikipedia)\n\n{top['snippet']}"
        return f" No Wikipedia results found for '{query}'"
    except Exception as e:
        return f" Wikipedia search error: {e}"
    
def get_weather(city: str) -> str:
    """Get current weather for any city. FREE — no API key needed!"""
    print(f"\n [TOOL CALLED] Weather for: '{city}'")
    try:
        url = f"https://wttr.in/{city.replace(' ', '+')}?format=3"
        response = requests.get(url, timeout=20, headers={"User-Agent": "curl/7.68"})

        if response.status_code == 200:
            return f" **Weather for {city}:**\n{response.text.strip()}"

        return f" Could not get weather for '{city}'"

    except Exception as e:
        return f" Weather lookup error: {e}"
    
def get_current_time() -> str:
    """Return the current date and time. No API needed — just Python!"""
    from datetime import datetime
    now = datetime.now()
    return f" Current time: **{now.strftime('%A, %B %d, %Y at %I:%M %p')}**"

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": (
                "Search Wikipedia for information about any topic, person, place, "
                "event, concept, or technology. Use this when the user asks factual "
                "questions or wants to learn about something."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic or question to search on Wikipedia"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get the current weather for any city in the world. "
                "Use this when the user asks about weather, temperature, or climate in a location."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name to get weather for (e.g., 'Mumbai', 'New York', 'London')"
                    }
                },
                "required": ["city"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time. Use when user asks what time or date it is.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    }
]

def handle_tool_calls(message)->list:
    """
    Execute the Python functions requested by the LLM
    and return the results formatted for the API.
    """
    responses=[]
    
    if not message.tool_calls:
        return responses
    
    for tool_call in message.tool_calls:
        function_name=tool_call.function.name
        arguments=json.loads(tool_call.function.arguments)
        print(f" Running tool: {function_name} with args: {arguments}")
        try:
            if function_name=="search_wikipedia":
                query=arguments.get("query")
                result=search_wikipedia(query)
            elif function_name == "get_weather":
                # Get the city parameter
                city = arguments.get("city")
                result = get_weather(city)
                
            elif function_name == "get_current_time":
                # No arguments needed
                result = get_current_time()
                
            else:
                result = f"❌ Unknown tool name: {function_name}"
        except Exception as e:
            result = f"❌ Error executing tool {function_name}: {e}"
            
        responses.append({
            "role":"tool",
            "content":result,
            "tool_call_id": tool_call.id
        })
    return responses

def summarize_url(url: str,model_choice:str):
    """
    Fetch a website URL, scrape its clean text,
    send it to the LLM, and stream back a structured summary.
    """
    
    if not url:
        yield "Please provide a URL to summarize."
        return
    if not url.startswith("http"):
        url="https://"+url
    yield"feeticng content from url"
    
    content=fetch_website_contents(url)
    if content.startswith("⚠️"):
        yield content
        return
    
    yield f"Scraped {len(content):,} characters from webpage.\n\n---\n\n⏳ Generating AI summary...\n\n"
    
    client,model=get_client_and_model(model_choice)
    
    messages=[
        {
            "role":"system","content":SUMMARY_SYSTEM_PROMPT
        },
        {
            "role":"user","content":f"Please summarize this webpage:\n\nURL: {url}\n\nContent:\n{content}"
        }
    ]
    try:
        stream=client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        result = f" **Summary complete!** (from {url})\n\n---\n\n"
        for chunk in stream:
            piece=chunk.choices[0].delta.content or ""
            result+=piece
            
            yield result
    except Exception as e:
        yield f" AI generation error: {e}\n\nCheck that your API key is correct and Ollama is running if using Llama."
        
def extract_facts(url:str, model_choice:str)->str:
    """Fetch a webpage, extract all key facts using AI,
    and return them in a structured markdown list.
    """
    
    if not url:
       return json.dumps({"error": "Please enter a URL first"}, indent=2)
    if not url.startswith("http"):
        url="https://"+url
    
    
    content=fetch_website_contents(url)

    if content.startswith("⚠️"):
        return json.dumps({"error":content},indent=2)
    
    client,model=get_client_and_model(model_choice)
    
    messages = [
        {
            "role": "system",
            "content": """You are a fact extractor. Analyze the content and return ONLY valid JSON.

            Use exactly this structure:
            {
            "page_title": "the title of the page",
            "main_topic": "what this page is mainly about in one sentence",
            "key_facts": ["fact 1", "fact 2", "fact 3", "fact 4", "fact 5"],
            "people_mentioned": ["person 1", "person 2"],
            "organizations_mentioned": ["org 1", "org 2"],
            "locations_mentioned": ["city1", "country1"],
            "dates_mentioned": ["date 1", "date 2"],
            "sentiment": "positive OR negative OR neutral OR mixed",
            "complexity_level": "beginner OR intermediate OR advanced",
            "estimated_read_time": "X minutes",
            "summary_one_line": "one sentence summary of the entire page"
            }

            Return ONLY the JSON object. Do not include any markdown backticks, explanations, or text surrounding the JSON."""
        },
        {
            "role": "user",
            "content": f"Extract facts from this webpage content (limit analysis to the first 4000 characters):\n\nURL: {url}\n\nContent:\n{content[:4000]}"
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type":"json_object"}
        )
        
        raw_json_string=response.choices[0].message.content
        parsed_dict=json.loads(raw_json_string)

        return json.dumps(parsed_dict,indent=2)
    except Exception as e:
        # Return the error formatted as JSON
        return json.dumps({"error": f"Could not extract facts: {e}"}, indent=2)
    

page_context={"text":"","url":""}
def chat(message: str, history: list, model_choice: str):
    """
    Main chat handler.
    1. Re-builds conversation history safely.
    2. Inject scraped webpage context if available.
    3. Handles the tool calling loop.
    4. Streams the final reply chunk-by-chunk by updating history.
    """
    # Convert history elements safely to raw dictionaries
    safe_history = []
    for h in history:
        if isinstance(h, dict):
            safe_history.append({"role": h.get("role", ""), "content": h.get("content", "")})
        else:
            role = getattr(h, "role", "")
            content = getattr(h, "content", "")
            safe_history.append({"role": role, "content": content})

    # If the history is empty, do nothing
    if not safe_history:
        yield safe_history
        return

    client, model = get_client_and_model(model_choice)
    
    system = CHAT_SYSTEM_PROMPT
    if page_context["text"]:
        system += f"\n\n## Webpage Context loaded by User:\nURL: {page_context['url']}\n\nContent (use this to answer questions if asked):\n---\n{page_context['text'][:3000]}\n---"
        
    messages = [{"role": "system", "content": system}]
    messages.extend(safe_history)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools
        )
        
        while response.choices[0].finish_reason == "tool_calls":
            tool_message = response.choices[0].message
            tool_results = handle_tool_calls(tool_message)
            messages.append(tool_message) 
            messages.extend(tool_results) 
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools
            )
        
        final_stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        
        # Append a new empty assistant message bubble to history
        safe_history.append({"role": "assistant", "content": ""})
        
        result = ""
        for chunk in final_stream:
            piece = chunk.choices[0].delta.content or ""
            result += piece
            safe_history[-1]["content"] = result
            yield safe_history
            
    except Exception as e:
        safe_history.append({"role": "assistant", "content": f"❌ Chat error: {e}\n\nCheck that your API key is correct and Ollama is running if using Llama."})
        yield safe_history


def load_url_for_chat(url: str, model_choice: str):
    """
    Scrapes a webpage, saves it into global context,
    and then streams the summary back to the UI.
    """
    if not url:
        yield " Please enter a URL first."
        return

    clean_url = url if url.startswith("http") else "https://" + url

    # Scrape and save to the global page_context dict
    content = fetch_website_contents(clean_url)
    page_context["text"] = content
    page_context["url"]  = clean_url

    # Call summarize_url (yields chunks) to stream the summary
    for chunk in summarize_url(clean_url, model_choice):
        yield chunk


# ── CREATE GRADIO LAYOUT ─────────────────────────────────────
with gr.Blocks(
    title="ARIA — AI Research Assistant",
    theme=gr.themes.Soft()
) as app:

    # ── Header ──
    gr.Markdown("""
    #  ARIA — AI Research & Information Assistant
    **Built with:** Google Gemini (free cloud) + Ollama (local free) + Wikipedia + wttr.in weather
    
    *This project covers every concept from Week 1 + Week 2 of the LLM Engineering course.*
    """)

    # ── Model Dropdown (Switching between Gemini and local Llama) ──
    model_choice = gr.Dropdown(
        choices=[
            " Gemini Flash (Free Cloud)",
            " Llama3.2 (Free Local via Ollama)",
        ],
        value=" Gemini Flash (Free Cloud)",
        label=" Select AI Model",
        info="Gemini = Cloud (requires GEMINI_API_KEY in .env) | Llama = Local (requires Ollama running on your PC)"
    )

    # ── Tabs Navigation ──
    with gr.Tabs():

        # ── TAB 1: Webpage Summarizer ──
        with gr.Tab(" Summarize Webpage"):
            gr.Markdown("""
            ### Paste a URL to scrape it and generate a structured summary.
            *The scraped content will also be loaded into the **Chat** tab context so you can discuss it!*
            """)
            
            url_input = gr.Textbox(
                label=" Website URL",
                placeholder="https://en.wikipedia.org/wiki/Artificial_intelligence",
                info="Paste any article link, documentation page, or blog post."
            )
            
            with gr.Row():
                summarize_btn = gr.Button(" Summarize", variant="primary", scale=2)
                clear_btn     = gr.Button(" Clear",      variant="secondary", scale=1)
                
            summary_output = gr.Markdown(
                label=" AI Summary",
                value="*Your summary will appear here...*"
            )

            # Event: when clicking Summarize, run load_url_for_chat
            summarize_btn.click(
                fn=load_url_for_chat,
                inputs=[url_input, model_choice],
                outputs=summary_output
            )
            
            # Event: Clear fields
            clear_btn.click(
                fn=lambda: ("", "*Your summary will appear here...*"),
                outputs=[url_input, summary_output]
            )

        # ── TAB 2: Chat ──
        with gr.Tab(" Chat with ARIA"):
            gr.Markdown("""
            ### Conversational Assistant with Memory & Tools.
            **Ask ARIA anything! She has direct access to:**
            -  Wikipedia (factual searches)
            -  Weather data (wttr.in lookup)
            -  Time (system clock)
            -  The webpage you loaded in the **Summarize** tab!
            """)

            chatbot = gr.Chatbot(
                value=[],
                height=400,
                type="messages",
                label=" Chatbox",
                placeholder="Ask ARIA about the loaded page, current weather, Wikipedia facts, etc."
            )

            with gr.Row():
                chat_input = gr.Textbox(
                    label="Type your message:",
                    placeholder='Try: "What is machine learning?" or "Weather in Tokyo?"',
                    scale=5,
                    lines=1
                )
                send_btn = gr.Button("Send ▶", variant="primary", scale=1)

            clear_chat_btn = gr.Button(" Clear Chat History", variant="secondary")

            # Helper functions for handling the chat submit flow
            def add_message_to_chatbot(msg, chat_history):
                chat_history.append({"role": "user", "content": msg})
                return "", chat_history

            # Wire up chat submit events (hitting Enter or clicking Send)
            chat_input.submit(
                fn=add_message_to_chatbot,
                inputs=[chat_input, chatbot],
                outputs=[chat_input, chatbot]
            ).then(
                fn=chat,
                inputs=[chat_input, chatbot, model_choice],
                outputs=chatbot
            )

            send_btn.click(
                fn=add_message_to_chatbot,
                inputs=[chat_input, chatbot],
                outputs=[chat_input, chatbot]
            ).then(
                fn=chat,
                inputs=[chat_input, chatbot, model_choice],
                outputs=chatbot
            )

            clear_chat_btn.click(fn=lambda: [], outputs=chatbot)

        # ── TAB 3: Extract Facts (JSON) ──
        with gr.Tab(" Extract Facts (JSON)"):
            gr.Markdown("""
            ### Scrape a website and extract structured data as JSON.
            *Forces the model to only output a valid JSON object (`response_format=json_object`).*
            """)

            facts_url = gr.Textbox(
                label=" Webpage URL to analyze",
                placeholder="https://en.wikipedia.org/wiki/Python_(programming_language)"
            )

            extract_btn = gr.Button(" Extract Facts", variant="secondary")

            facts_output = gr.Code(
                label=" Extracted Facts (JSON)",
                language="json",
                value='{\n  "message": "Enter a URL and click Extract Facts to see structured data"\n}'
            )

            # Event: click Extract -> runs extract_facts
            extract_btn.click(
                fn=extract_facts,
                inputs=[facts_url, model_choice],
                outputs=facts_output
            )

        # ── TAB 4: Course Reference Help ──
        with gr.Tab(" Help & Reference"):
            gr.Markdown("""
            ##  Course Concepts Implemented in ARIA
            
            | Feature | Concept | Week + Day |
            |---|---|---|
            | **Model Dropdown** | OpenAI-compatible endpoints switching | Week 1 Day 2 |
            | **Scraper** | Fetching & cleaning HTML | Week 1 Day 1 |
            | **Summarize URL** | System/User prompts + Streaming outputs | W1 D1, W1 D5, W2 D2 |
            | **Chat Memory** | Rebuilding context list from Gradio history | Week 1 Day 4 |
            | **Wikipedia Search** | Tool calling schema + lookup | Week 2 Day 4 |
            | **Weather lookup** | Tool calling with argument parser | Week 2 Day 4 |
            | **Extract Facts** | Forcing JSON output (`json_object`) | Week 1 Day 5 |
            | **UI Tabs Layout** | gr.Blocks custom UI organization | Week 2 Day 5 |
            
            ---
            ##  Troubleshooting
            - **Ollama fails:** Make sure the Ollama application is running on your machine (`ollama serve`) and you have pulled the model (`ollama pull llama3.2`).
            - **Gemini fails:** Check your `.env` file key. It should print ` Gemini key loaded!` in the console logs when launching this script.
            """)


# ── LAUNCH THE WEB SERVER ────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print(" ARIA — AI Research & Information Assistant")
    print("="*50)
    print("\n Starting Gradio application...")
    print("   Your browser will open automatically at: http://localhost:7860")
    print("\n Tip: Scrape a page first, then chat about it!")
    print("="*50 + "\n")
    
    app.launch(inbrowser=True)
