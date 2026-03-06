from litellm import completion
import time

MODEL = "gpt-4.1-nano"

SYSTEM_PROMPT = """
Extract structured information from the job description.

Return EXACTLY this format:

Experience: <number of years OR Not specified>
Skills: <comma separated list>

Rules:
- If years of experience appear (e.g., 3 years, 5+ years, 2-4 years), extract them.
- If none appear, return: Not specified
- Skills must be comma separated.
"""


def extract_fields(description, retries=3):

    for attempt in range(retries):

        try:

            response = completion(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": description}
                ],
                temperature=0
            )

            return response.choices[0].message.content

        except Exception as e:

            if attempt < retries - 1:
                time.sleep(2)
            else:
                raise e