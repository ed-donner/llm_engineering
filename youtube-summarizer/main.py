
from openai import OpenAI
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

# Load environment variables
load_dotenv(override=True)

# Create OpenAI client
client = OpenAI()

# Ask user for YouTube URL
url = input("Paste YouTube URL:\n")

# Extract video ID
video_id = url.split("v=")[1]

# Create transcript API object
ytt_api = YouTubeTranscriptApi()

# Fetch transcript
# transcript_data = ytt_api.fetch(video_id)

transcript_data = ytt_api.fetch(video_id, languages=['hi'])
# Combine transcript text
full_transcript = " ".join(
    [item.text for item in transcript_data]
)

# Messages for AI
messages = [
    {
        "role": "system",
        "content": "You are a helpful YouTube video summarizer."
    },
    {
        "role": "user",
        "content": f"Summarize this transcript:\n\n{full_transcript}"
    }
]

# Send request to OpenAI
response = client.chat.completions.create(
    model="gpt-5-nano",
    messages=messages
)

# Print summary
print("\nSUMMARY:\n")
print(response.choices[0].message.content)
