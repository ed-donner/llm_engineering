import json
import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()


@app.post("/translate-json")
async def translate_json(payload: Dict[str, Any]):
    try:
        json_response = json.dumps(payload)

        user_prompt = f"""
        Translate the following JSON field names and their corresponding values into Spanish.
        Keep the structure exactly the same.
        Do not modify the values.
        Return only valid JSON.

        {json_response}
        """

        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"},
            temperature=0,
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
