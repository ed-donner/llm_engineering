import os  # Import os to read environment variables from the operating system.
from dotenv import load_dotenv
from posthog import api_key  # Import load_dotenv to load variables from the .env file.
from lobsters_scraper import scrape_lobsters  # Import the scraper function that returns active stories and latest comments.
from openai import OpenAI  # Import the OpenAI client.

# use open source model from ollama
OLLAMA_BASE_URL = "http://localhost:11434/v1"
ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')


system_prompt = """
You are a sharp technical news analyst summarizing scraped content from Lobsters.

You will receive two datasets:
1. Active stories: titles and links from the Lobsters Active page.
2. Latest comments: story titles and user comments from the Lobsters Comments page.

Your job:
- Summarize the main technical themes.
- Identify interesting engineering discussions.
- Extract useful insights from comments.
- Mention relevant programming languages, tools, frameworks, systems, or security topics.
- Ignore navigation text, repeated boilerplate, and irrelevant page UI.
- Do not invent details that are not present in the provided data.
- Keep the tone lightly witty, but still useful and professional.
- Respond in Thai.
- Format the response in Markdown.
- Do not wrap the response in a code block.

Required structure:
1. Start with one short intro summary.
2. Then provide concise bullet points.
3. End with a short conclusion or takeaway for developers.
"""  # Define the system-level instruction that controls the assistant's role, tone, and output format.


def build_lobsters_context(active_data, comments_data):  # Define a helper function to convert scraped data into clean plain text.
    lines = []  # Create an empty list to collect text lines.

    lines.append("# Active Stories")  # Add a section header for active stories.
    lines.append("")  # Add an empty line for readability.

    for item in active_data:  # Loop through each active story item.
        lines.append(f"{item['number']}. {item['title']}")  # Add the story number and title.
        lines.append(f"   Link: {item['link']}")  # Add the story link.
        lines.append("")  # Add an empty line between stories.

    lines.append("# Latest Comments")  # Add a section header for latest comments.
    lines.append("")  # Add an empty line for readability.

    for item in comments_data:  # Loop through each latest comment item.
        comment = item["comment"]  # Store the comment text in a local variable.

        if len(comment) > 1200:  # Limit very long comments to keep the prompt compact.
            comment = comment[:1200] + "..."  # Truncate the comment and add an ellipsis.

        lines.append(f"{item['number']}. Story: {item['title']}")  # Add the related story title.
        lines.append(f"   Comment: {comment}")  # Add the comment text.
        lines.append("")  # Add an empty line between comments.

    return "\n".join(lines)  # Join all lines into one plain-text context string.


def messages_for(active_data, comments_data):  # Define a function that builds the message list for the model.
    lobsters_context = build_lobsters_context(active_data, comments_data)  # Convert scraped data into clean text.

    user_prompt = f"""
Here is the scraped Lobsters data.

Please summarize it based only on the information below.

Focus on:
- Main technical topics
- Interesting stories
- Useful comment insights
- Programming languages, tools, frameworks, infrastructure, or security topics
- Practical takeaways for developers

Data:

{lobsters_context}
"""  # Create the user prompt and insert the scraped Lobsters context.

    return [  # Return the message list required by the Chat Completions API.
        {"role": "system", "content": system_prompt},  # Provide the model behavior, tone, and rules.
        {"role": "user", "content": user_prompt}  # Provide the actual scraped data and summarization request.
    ]


def summarize_lobsters(active_data, comments_data):  # Define a function that sends scraped data to the model and returns the summary.
    response = ollama.chat.completions.create(  # Create a chat completion request.
        model="llama3.2:1B",  # Choose the model used for summarization.
        messages=messages_for(active_data, comments_data)  # Build and pass the messages into the model.
    )  # End the API request.

    return response.choices[0].message.content  # Return the generated summary text.


def main():
    active_data, comments_data = scrape_lobsters()

    summary = summarize_lobsters(active_data, comments_data)

    print("\n=== Lobsters AI Summary ===\n")
    print(summary)

    with open("lobsters_summary.md", "w", encoding="utf-8") as f:
        f.write(summary)


if __name__ == "__main__":  # Run the script only when this file is executed directly.
    main()  # Start the main workflow.