import streamlit as st
from langchain_community.document_loaders import YoutubeLoader, UnstructuredURLLoader
import validators
from openai import OpenAI
import os
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

from dotenv import load_dotenv
# Load environment variables
load_dotenv()

if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")

# Streamlit page setup
st.set_page_config(page_title="Summarize text from YouTube or Website", page_icon="📄")
st.title("LangChain: Summarize Content from YouTube or Website")
st.subheader("Enter a URL below")

# Input URL
generic_url = st.text_input("URL", label_visibility="collapsed").strip()

# Custom headers for web scraping
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 "
        "Edg/120.0.0.0"
    )
}

# System prompt
system_prompt = """
You are an expert assistant specialized in analyzing content from  YouTube videos and websites.
You will be given the full transcript or text content, and you need to summarize it clearly and concisely.
"""

#User prompt
userPrompt="""
Provide the summary of the following content
"""

# Button action
if st.button("Summarize the content from URL or YouTube"):
    if not validators.url(generic_url):
        st.error("Please enter a valid URL.")
    else:
        try:
            with st.spinner("Fetching and summarizing content..."):
                # Load content
                if "youtube.com" in generic_url:
                    loader = YoutubeLoader.from_youtube_url(youtube_url= generic_url)

                else:
                    loader = UnstructuredURLLoader(
                        urls=[generic_url],
                        ssl_verify=False,
                        headers=headers
                    )

                documents = loader.load()
                print(documents)
                if not documents:
                    st.error("Could not extract content from the URL or YouTube video.")
                else:
                    # Extract plain text from loaded documents
                    page_text = ""
                    for doc in documents:
                        page_text += doc.page_content + "\n"

                    if not page_text.strip():
                        st.error("No text content could be extracted.")
                    else:
                        response = client.chat.completions.create(model="gpt-4o-mini",
                        messages=[{"role":"system", "content":system_prompt}, {"role":"user", "content":userPrompt + "\n" +page_text}],
                        temperature=0.2,
                        max_tokens=512)
                        st.success("Summary:")
                        st.write(response.choices[0].message.content)

        except Exception as e:
            st.exception(f"An error occurred: {e}")
