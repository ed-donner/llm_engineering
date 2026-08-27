import os
import streamlit as st
import requests
import json
import warnings
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse

# Auto-load the GROQ_API_KEY from your local .env file
load_dotenv()
SYSTEM_ENV_KEY = os.getenv("GROQ_API_KEY", "")

warnings.filterwarnings("ignore")

# --- INITIALIZE COHESIVE CONFIGURATION ---
st.set_page_config(
    page_title="Suzume — Web Portal & Summarizer",
    page_icon="🚪",
    layout="wide" 
)

# --- ✨ MAGICAL GLASSMORPHISM & HIGH-CONTRAST CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@700&family=Quicksand:wght@500;700&display=swap');
    
    /* Suzume Dreamy Sky-Blue to Overflooded Water Canvas Gradient */
    .stApp {
        background: linear-gradient(180deg, #b3e5fc 0%, #e0f7fa 40%, #80deea 100%) !important;
        font-family: 'Quicksand', sans-serif;
    }
    
    /* ✨ WHIMSY UPGRADE: Frosted Glass Containers (Glassmorphism) */
    div[data-testid="stContainer"] {
        background: rgba(255, 255, 255, 0.6) !important; /* Semi-transparent white */
        backdrop-filter: blur(12px) !important; /* Frosted glass blur effect */
        -webkit-backdrop-filter: blur(12px) !important;
        border: 2px solid rgba(255, 255, 255, 0.8) !important; /* Soft glowing border */
        border-radius: 24px !important;
        padding: 25px !important;
        box-shadow: 0px 15px 35px rgba(0, 96, 100, 0.15) !important;
        margin-bottom: 25px !important;
    }
    
    /* 🛠️ THE FIX: Deep Midnight Teal Headers for Perfect Contrast */
    h1, h2, h3, h4, .stMarkdown h2, .stMarkdown h3 {
        color: #003333 !important; /* Very dark teal/navy */
        font-family: 'Comfortaa', sans-serif;
        font-weight: 800 !important;
        border-bottom: none !important;
    }
    
    /* Typography Overrides - Crisp Jet Black Body text */
    .stMarkdown, p, span, label, li {
        color: #111111 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    
    .subtitle {
        text-align: center;
        color: #004d40 !important;
        font-size: 1.2rem !important;
        font-weight: bold;
        margin-bottom: 35px;
    }
    
    /* Input and Dropdown Overrides */
    div.stTextInput input, div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #111111 !important;
        border: 2px solid #00838f !important;
        border-radius: 12px !important;
    }
    
    /* ✨ WHIMSY UPGRADE: Floating Image Animation */
    [data-testid="stImage"] img {
        border-radius: 16px !important;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.15) !important;
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    /* Primary Deep Water Gate-keeper Action Button */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #00838f 0%, #006064 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 16px !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        padding: 12px 0px !important;
        box-shadow: 0px 8px 15px rgba(0,96,100,0.3) !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0px 12px 20px rgba(0,96,100,0.5) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- LIGHTNING-FAST INFERENCE STREAM (GROQ) ---
def query_groq_stream(prompt_text, system_instruction, api_key):
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.5, # Slightly increased for more creative tone options
            stream=True
        )
        for chunk in completion:
            chunk_text = chunk.choices[0].delta.content
            if chunk_text:
                yield chunk_text
    except Exception as e:
        yield f"\n\n❌ Celestial gateway path error: {e}"

# --- MAP-REDUCE TEXT CHUNKER ---
def chunk_text_by_paragraphs(text, max_chars=4000):
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        cleaned_para = para.strip()
        if not cleaned_para:
            continue
        if len(current_chunk) + len(cleaned_para) < max_chars:
            current_chunk += cleaned_para + "\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = cleaned_para + "\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks

# --- WEBPAGE TEXT & IMAGE EXTRACTION LOGIC ---
def scrape_webpage_data(target_url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pull featured image
        featured_image_url = None
        og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
        if og_img and og_img.get("content"):
            featured_image_url = og_img.get("content")
        else:
            img_tags = soup.find_all("img")
            for img in img_tags:
                src = img.get("src") or img.get("data-src")
                if src and any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    if "logo" not in src.lower() and "icon" not in src.lower():
                        featured_image_url = src
                        break
                        
        if featured_image_url and not urlparse(featured_image_url).scheme:
            featured_image_url = urljoin(target_url, featured_image_url)

        # Extract paragraphs
        for element in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
            element.extract()
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 15]
        clean_text = "\n".join(paragraphs) if paragraphs else None
        
        return clean_text, featured_image_url
    except Exception as e:
        st.error(f"🚪 Missing road trail: {e}")
        return None, None

# --- FRONTEND INTERFACE ---
st.markdown("<h1>🚪 すずめ (Suzume) Web Portal</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>✨ Open the Door to Any Web Scroll with Personalized Ingestion Tuning ✨</div>", unsafe_allow_html=True)

active_api_key = SYSTEM_ENV_KEY

# Layout centering
_, main_col, _ = st.columns([1, 4, 1])

with main_col:
    with st.container():
        st.subheader("🌾 Step 1: Content Scraper Target")
        url_input = st.text_input(
            "Paste the web link scroll you want to ingest:", 
            placeholder="https://en.wikipedia.org/wiki/..."
        )
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.subheader("🔮 Step 2: Personalization Options")
        
        col1, col2 = st.columns(2)
        with col1:
            summary_length = st.selectbox(
                "Select Summary Resolution Depth:",
                options=["Brief Takeaways (3 Bullets)", "Standard Synthesis (5 Bullets)", "Comprehensive Narrative"]
            )
        with col2:
            summary_tone = st.selectbox(
                "Select Expressive Narrative Tone:",
                options=["Professional & Fact-Dense", "Casual & Simplified", "Whimsical & Mystical Tale ✨"]
            )
            
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        submit_button = st.button("Unlock and Summarize Page 🚪✨", use_container_width=True)

# Execution Pipeline
if submit_button:
    if not active_api_key:
        st.error("⚠️ Ingestion halted: Please map your Groq API Key into your workspace settings.")
    elif not url_input:
        st.warning("⚠️ Portal entry empty: Please pass an active target link string vector first.")
    else:
        raw_content = None
        image_link = None
        intermediate_summaries = []
        
        with st.status("🌊 Opening the conceptual gate and processing data...", expanded=True) as status:
            st.write("🔍 Extracting text layers and seeking media visual hooks...")
            raw_content, image_link = scrape_webpage_data(url_input)
            
            if raw_content:
                text_chunks = chunk_text_by_paragraphs(raw_content, max_chars=4000)
                num_chunks = len(text_chunks)
                st.write(f"📋 Managed document split cleanly into {num_chunks} segments.")
                
                for i, chunk in enumerate(text_chunks):
                    st.write(f"🧩 Processing fragment matrix {i+1} of {num_chunks} via Groq pipeline...")
                    instruction = "Extract all critical events, names, dates, metrics, and primary assertions into a clear, dense note structure."
                    chunk_summary_stream = query_groq_stream(chunk, instruction, active_api_key)
                    chunk_summary = "".join(list(chunk_summary_stream))
                    intermediate_summaries.append(chunk_summary)
                    
                status.update(label="🌱 Web Ingestion Complete!", state="complete", expanded=False)
            else:
                status.update(label="🍂 The structural door jammed.", state="error")
                st.error("The parser could not locate any standard paragraph layers on this target link.")

        # SIDE BY SIDE LAYOUT
        if raw_content and intermediate_summaries:
            st.markdown("---")
            
            col_image, col_text = st.columns([1, 2], gap="large")
            
            with col_image:
                if image_link:
                    st.subheader("🖼️ Target Context")
                    st.image(image_link, use_container_width=True)
                else:
                    st.info("No primary image detected on this specific page.")
                    
            with col_text:
                st.subheader(f"📋 Takeaways ({summary_length})")
                
                # Instruct the AI to use special bullets if the whimsical tone is selected!
                bullet_style = "Use magical symbols (like ✦ or ✨) instead of standard bullet points." if "Whimsical" in summary_tone else "Use standard bullet points."
                
                system_directive = f"Synthesize these notes into the following format: {summary_length}. Mimic this personality profile perfectly: {summary_tone}. {bullet_style} Write vividly and with high factual accuracy."
                master_prompt = "\n".join(intermediate_summaries)
                
                final_text_placeholder = st.empty()
                compiled_live_text = ""
                
                for token in query_groq_stream(master_prompt, system_directive, active_api_key):
                    compiled_live_text += token
                    final_text_placeholder.markdown(compiled_live_text)
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("👀 View Raw Text Data Log"):
                st.text_area("Extracted Web Tapestry", raw_content[:4000] + "\n\n[Truncated...]", height=200, disabled=True)