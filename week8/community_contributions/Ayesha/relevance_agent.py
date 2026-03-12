import json
import re
from openai import OpenAI
from config import OPENROUTER_BASE, OPENROUTER_API_KEY, MODEL_RELEVANCE

client = OpenAI(base_url=OPENROUTER_BASE, api_key=OPENROUTER_API_KEY)


SYSTEM_PROMPT = """
You are a research assistant.

Select the 7 most interesting papers related to:
- AI
- Healthcare
- Human Computer Interaction

Return JSON only in this format:

{
 "papers":[
  {"title":"...", "reason":"...", "url":"..."}
 ]
}
"""


def select_papers(papers):

    content = "\n\n".join([p.describe() for p in papers])

    response = client.chat.completions.create(
        model=MODEL_RELEVANCE,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
    )

    text = response.choices[0].message.content

    print("LLM raw response:\n", text)

    # remove markdown code fences if present
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text).strip()

    try:
        data = json.loads(text)
        papers = data.get("papers", [])

        print("Parsed papers:", len(papers))

        return papers

    except Exception as e:

        print("JSON parsing failed:", e)
        print("Cleaned text was:\n", text)

        return []