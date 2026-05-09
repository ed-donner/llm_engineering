import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv


MODEL_LLAMA = 'llama3.2'
LLAMA_URL = "http://localhost:11434/v1"

MODEL_GPT = "gpt-5.4-mini"

load_dotenv(override=True)
OPENAI_KEY = os.getenv("OPEN_API_KEY")

def get_LLM(local= False):
    client = None
    if local:
        client = OpenAI(base_url=LLAMA_URL,api_key="ollama")
        print(f'Serving local model')
    else:
        client = OpenAI()
        print(f'Serving PAID model')
    return client

def getModel(local = False):
    if local:
        return MODEL_LLAMA
    else:
        return MODEL_GPT

client = get_LLM()
mod = getModel()
response = client.chat.completions.create(model= mod,
    messages=[{"role":"user","content":"Tell me a joke"}]
    )
    
print(response.choices[0].message.content)

# 1. Initialize the app first
app = FastAPI()

# 2. Add middleware IMMEDIATELY after initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Setup Client (Ensure your key is valid)
#load_dotenv(override=True)
#OpenAI_key = os.getenv('OPENAI_API_KEY')


#if OpenAI_key.startswith('sk-'):
 #print('fine key')



class WritingDraft(BaseModel):
    text: str

@app.post("/analyze")
async def analyze_writing(draft: WritingDraft):
    try:
        print(f"--- Processing New Draft ({len(draft.text)} chars) ---")
                
        system_prompt2 = """You are an expert tutor in Non-Narrative writing for Selective Tests in Australia. 
        Assess the writing based STRICTLY on the provided rubrics for Content, Form, Organisation, Style, and Expression.
        Provide a score out of 25.
        Output MUST be a valid JSON object only. No markdown, no code blocks, no preamble. For Detailed Analysis results You MUST focus only on the most important 5 improvements which will maximise the score.

        RUBRICS:
        [Content, Form, Organisation & Style]
        1. Addresses stimulus/audience.
        2. 3 main ideas, each with 3 sub-points (9 total).
        3. Coherent paragraphs/cohesive devices.
        4. Mature/interesting ideas.
        5. Appropriate text type features (voice, tense, modality).
        6. Sophisticated vocabulary.
        7. Deliberate style/special techniques.

        [Expression]
        1. Varied sentence lengths (compound/complex).
        2. Flow and tension via sentence types.
        3. Logical flow, no redundancy/verbosity.
        4. Grammar, punctuation, and spelling accuracy.

        REQUIRED JSON STRUCTURE:
        {
        "Overall score out of 25": "number",
        "Details": [
            {
            "Line number which violates rubric item": "number",
            "Extract which violates rubric": "string",
            "Which rubric item it violates": "string",
            "Reason for violating rubric": "string",
            "Improvement with example": "string"
            }
        ],
        "Detailed Feedback": {
            "Good": "string (encouraging and enthusiastic)",
            "Improve": "string (concise and precise with examples)"
        }
        }

        VERY VERY IMPORTANT FOR DETAILS
        1. DO ensure the tone is ECOURAGING at all times
        2. DO ensure examples are clear
        3. DO NOT include invalid line numbers
        4. DO NOT include more than 5 most important changes in the Details array. 
          
        """
        
        response = client.chat.completions.create(
            model=mod, #MODEL_GPT, 
            messages=[
                {"role": "system", "content": system_prompt2},
                {"role": "user", "content": draft.text}
            ],
            response_format={"type": "json_object"}
        )
        
        # CORRECTED ACCESS:
        # Use .choices[0].message.content for the latest SDK
        content = response.choices[0].message.content
        
        result = json.loads(content)
        print(f"--- Analysis Successful ---\n {result}")
        return result

    except Exception as e:
        print(f"BACKEND ERROR: {str(e)}")
        # Log the full error to see if it's a versioning issue
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# 4. Run command must be at the very bottom
if __name__ == "__main__":
    import uvicorn
    # Do NOT use reload=True if running via this block to avoid middleware issues
    uvicorn.run(app, host="127.0.0.1", port=8000)
   # uvicorn.run(app, host="0.0.0.0", port=8080)

