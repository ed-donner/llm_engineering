# I have used the youtube_transcript_api to get the transcript of the video
# I have used the openai to get the summary of the video

from openai import OpenAI
from dotenv import load_dotenv
import os
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()
api = YouTubeTranscriptApi()
video_id = "y8AXgTBdY5E"
transcript = (
    api.list(video_id)
    .find_generated_transcript(["hi"])
    .fetch()
)
text = " ".join([t.text for t in transcript])

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "system", "content": "i want you think like pure RCB fan"},
        {"role": "user", "content": "create the summary in english in for this news" + text}
    ]
)
print(response.choices[0].message.content)