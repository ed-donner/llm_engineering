import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from main import scrape_website

from llm import (
    generate_brochure_content,
    generate_image_prompt
)

from image_generator import generate_image

from pdf_generator import create_brochure_pdf


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Brochure Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# PRODUCTION-LEVEL CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    /* ===== GLOBAL RESET & BASE ===== */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* ===== MAIN CONTAINER ===== */
    .stApp {
        background: #0a0e1a;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1.5rem;
    }
    
    /* ===== GLASSMORPHISM EFFECT ===== */
    .glass {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    /* ===== HEADER SECTION ===== */
    .hero-section {
        background: linear-gradient(135deg, #0a0e1a 0%, #1a1040 40%, #0d1b2a 100%);
        padding: 3.5rem 3rem;
        border-radius: 24px;
        margin-bottom: 2.5rem;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        animation: float 20s ease-in-out infinite;
    }
    
    .hero-section::after {
        content: '';
        position: absolute;
        bottom: -30%;
        left: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(236, 72, 153, 0.1) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        animation: float 25s ease-in-out infinite reverse;
    }
    
    @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(30px, -30px) scale(1.1); }
        66% { transform: translate(-20px, 20px) scale(0.9); }
    }
    
    .hero-content {
        position: relative;
        z-index: 1;
    }
    
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(236, 72, 153, 0.2));
        padding: 0.4rem 1.2rem;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #818cf8;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border: 1px solid rgba(99, 102, 241, 0.2);
        margin-bottom: 1.2rem;
        backdrop-filter: blur(10px);
    }
    
    .hero-title {
        font-size: 3.2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.8rem !important;
        line-height: 1.2 !important;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        font-size: 1.15rem !important;
        color: rgba(255, 255, 255, 0.6) !important;
        max-width: 600px;
        line-height: 1.7 !important;
        font-weight: 400;
    }
    
    /* ===== INPUT SECTION ===== */
    .input-container {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        transition: all 0.4s ease;
    }
    
    .input-container:hover {
        border-color: rgba(99, 102, 241, 0.2);
        box-shadow: 0 8px 40px rgba(99, 102, 241, 0.05);
    }
    
    .input-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        letter-spacing: 0.3px;
        margin-bottom: 1rem;
        display: block;
    }
    
    /* ===== CUSTOM INPUT ===== */
    .stTextInput > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div:hover {
        border-color: rgba(99, 102, 241, 0.3) !important;
        background: rgba(255, 255, 255, 0.07) !important;
    }
    
    .stTextInput > div > div:focus-within {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }
    
    .stTextInput > div > div > input {
        background: transparent !important;
        color: #ffffff !important;
        font-size: 1rem !important;
        padding: 0.9rem 1.2rem !important;
        border: none !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.3) !important;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.9rem 2.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3) !important;
        width: 100% !important;
        letter-spacing: 0.3px;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.6s ease;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.5) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* ===== STEP CARDS ===== */
    .step-container {
        position: relative;
        padding-left: 2rem;
    }
    
    .step-container::before {
        content: '';
        position: absolute;
        left: 6px;
        top: 0;
        bottom: 0;
        width: 2px;
        background: linear-gradient(to bottom, #6366f1, #a855f7, #ec4899);
        opacity: 0.3;
    }
    
    .step-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        position: relative;
        transition: all 0.4s ease;
        animation: slideUp 0.6s ease;
    }
    
    .step-card:hover {
        border-color: rgba(99, 102, 241, 0.2);
        background: rgba(255, 255, 255, 0.05);
        transform: translateX(5px);
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .step-number-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        border-radius: 50%;
        font-weight: 700;
        font-size: 0.85rem;
        color: white;
        margin-right: 12px;
        flex-shrink: 0;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }
    
    .step-header {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .step-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: -0.01em;
    }
    
    .step-status {
        margin-left: auto;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.2rem 0.8rem;
        border-radius: 50px;
        background: rgba(99, 102, 241, 0.15);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.1);
    }
    
    /* ===== SUCCESS / ERROR / WARNING ===== */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid !important;
        padding: 1rem 1.5rem !important;
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stAlert[data-baseweb="notification"] {
        background: rgba(255, 255, 255, 0.03) !important;
    }
    
    .element-container div[data-testid="stAlert"] {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 12px !important;
        color: rgba(255, 255, 255, 0.7) !important;
        padding: 0.8rem 1.5rem !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.06) !important;
        border-color: rgba(99, 102, 241, 0.2) !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.02) !important;
        border-radius: 0 0 12px 12px !important;
        padding: 1.5rem !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-top: none !important;
    }
    
    /* ===== JSON VIEWER ===== */
    .stJson {
        background: rgba(0, 0, 0, 0.3) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    .stJson pre {
        color: #a5b4fc !important;
    }
    
    /* ===== CONTENT CARDS ===== */
    .content-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        transition: all 0.3s ease;
    }
    
    .content-card:hover {
        border-color: rgba(99, 102, 241, 0.15);
    }
    
    .content-card h3 {
        color: #a5b4fc !important;
        font-weight: 600 !important;
        margin-bottom: 0.8rem !important;
        font-size: 1.1rem !important;
        letter-spacing: -0.01em;
    }
    
    .content-card p, .content-card li {
        color: rgba(255, 255, 255, 0.7) !important;
        line-height: 1.7 !important;
    }
    
    .content-card ul {
        list-style: none;
        padding: 0;
    }
    
    .content-card ul li {
        padding: 0.4rem 0;
        padding-left: 1.5rem;
        position: relative;
    }
    
    .content-card ul li::before {
        content: '▸';
        position: absolute;
        left: 0;
        color: #6366f1;
        font-weight: 700;
    }
    
    /* ===== IMAGE ===== */
    .stImage {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3) !important;
    }
    
    .stImage img {
        width: 100% !important;
        display: block !important;
    }
    
    /* ===== DIVIDER ===== */
    hr {
        margin: 2.5rem 0 !important;
        border: none !important;
        height: 1px !important;
        background: linear-gradient(to right, transparent, rgba(99, 102, 241, 0.2), rgba(168, 85, 247, 0.2), transparent) !important;
    }
    
    /* ===== SUBHEADER ===== */
    .stSubheader {
        color: #ffffff !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        font-size: 1.3rem !important;
        letter-spacing: -0.01em;
    }
    
    /* ===== SPINNER ===== */
    .stSpinner > div {
        border-color: #6366f1 !important;
        border-top-color: #a855f7 !important;
    }
    
    /* ===== DOWNLOAD BUTTON ===== */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #10b981 50%, #34d399 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.9rem 2.5rem !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3) !important;
        width: 100% !important;
        font-size: 1rem !important;
        letter-spacing: 0.3px;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(16, 185, 129, 0.5) !important;
    }
    
    /* ===== SUCCESS CARD ===== */
    .success-card {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.1), rgba(16, 185, 129, 0.05));
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 16px;
        padding: 2.5rem;
        text-align: center;
        margin: 1.5rem 0;
    }
    
    .success-card h2 {
        color: #34d399 !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .success-card p {
        color: rgba(255, 255, 255, 0.5) !important;
    }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #6366f1, #a855f7);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #818cf8, #c084fc);
    }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .hero-section {
            padding: 2rem 1.5rem;
        }
        
        .hero-title {
            font-size: 2rem !important;
        }
        
        .hero-subtitle {
            font-size: 1rem !important;
        }
        
        .input-container {
            padding: 1.5rem;
        }
        
        .step-card {
            padding: 1.2rem 1.2rem;
        }
        
        .content-card {
            padding: 1.2rem;
        }
    }
    
    /* ===== TEXT COLORS ===== */
    .stMarkdown p {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #ffffff !important;
    }
    
    /* ===== CODE / JSON ===== */
    .stJson code {
        color: #a5b4fc !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")


# ============================================================
# CHECK API KEY
# ============================================================

if not groq_api_key:

    st.error(
        "❌ GROQ_API_KEY not found."
    )

    st.info(
        "Please add GROQ_API_KEY to your .env file."
    )

    st.stop()


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=groq_api_key
)


# ============================================================
# HEADER - HERO SECTION
# ============================================================

st.markdown("""
<div class="hero-section">
    <div class="hero-content">
        <div class="hero-badge">🚀 AI-Powered Innovation</div>
        <h1 class="hero-title">AI Brochure Generator</h1>
        <p class="hero-subtitle">
            Transform any company website into a stunning, 
            professional AI-generated brochure in seconds
        </p>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# URL INPUT
# ============================================================

st.markdown("""
<div class="input-container">
    <label class="input-label">🌐 Enter Website URL</label>
""", unsafe_allow_html=True)

website_url = st.text_input(
    "Website URL",
    placeholder="https://www.python.org/",
    label_visibility="collapsed"
)

st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# GENERATE BUTTON
# ============================================================

generate = st.button(
    "🚀 Generate Brochure",
    type="primary",
    use_container_width=True
)


# ============================================================
# MAIN PROCESS
# ============================================================

if generate:

    # ========================================================
    # VALIDATE URL
    # ========================================================

    if not website_url:

        st.warning(
            "⚠️ Please enter a website URL first."
        )

        st.stop()


    # ========================================================
    # STEP 1 — SCRAPING
    # ========================================================

    st.divider()

    st.markdown("""
    <div class="step-container">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-number-badge">1</span>
            <span class="step-title">Website Scraping</span>
            <span class="step-status">● In Progress</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:

        with st.spinner(
            "🔄 Scraping website..."
        ):

            scraped_data = scrape_website(
                website_url
            )

        st.success(
            "✅ Website scraped successfully!"
        )

    except Exception as e:

        st.error(
            f"❌ Scraping failed: {e}"
        )

        st.stop()


    # ========================================================
    # SHOW SCRAPED DATA
    # ========================================================

    with st.expander(
        "🔍 View Scraped Website Data"
    ):

        st.json(
            scraped_data
        )


    # ========================================================
    # STEP 2 — BROCHURE CONTENT
    # ========================================================

    st.divider()

    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-number-badge">2</span>
            <span class="step-title">AI Brochure Content</span>
            <span class="step-status">● Generating</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:

        with st.spinner(
            "🧠 Groq is generating brochure content..."
        ):

            brochure_data = generate_brochure_content(
                client,
                scraped_data
            )

        st.success(
            "✅ Brochure content generated!"
        )

    except Exception as e:

        st.error(
            f"❌ AI content generation failed: {e}"
        )

        st.stop()


    # ========================================================
    # DISPLAY BROCHURE CONTENT
    # ========================================================

    st.markdown("""
    <div class="content-card">
    """, unsafe_allow_html=True)

    st.markdown(
        "### 🏢 Company Overview"
    )

    st.write(
        brochure_data.get(
            "company_overview",
            ""
        )
    )


    st.markdown(
        "### 🛠️ Products & Services"
    )

    for item in brochure_data.get(
        "products_services",
        []
    ):

        st.write(
            f"• {item}"
        )


    st.markdown(
        "### ⭐ Key Features"
    )

    for feature in brochure_data.get(
        "key_features",
        []
    ):

        st.write(
            f"• {feature}"
        )


    st.markdown(
        "### 🎯 Mission"
    )

    st.write(
        brochure_data.get(
            "mission",
            ""
        )
    )


    st.markdown(
        "### ℹ️ Important Information"
    )

    st.write(
        brochure_data.get(
            "important_information",
            ""
        )
    )

    st.markdown("</div>", unsafe_allow_html=True)


    # ========================================================
    # STEP 3 — IMAGE PROMPT
    # ========================================================

    st.divider()

    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-number-badge">3</span>
            <span class="step-title">AI Image Prompt</span>
            <span class="step-status">● Creating</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:

        with st.spinner(
            "✍️ Creating image prompt..."
        ):

            image_prompt = generate_image_prompt(
                client,
                brochure_data
            )

        st.success(
            "✅ Image prompt created!"
        )

    except Exception as e:

        st.error(
            f"❌ Image prompt generation failed: {e}"
        )

        st.stop()


    with st.expander(
        "🎨 View Generated Image Prompt"
    ):

        st.write(
            image_prompt
        )


    # ========================================================
    # STEP 4 — FLUX IMAGE
    # ========================================================

    st.divider()

    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-number-badge">4</span>
            <span class="step-title">AI Image Generation</span>
            <span class="step-status">● Generating</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:

        with st.spinner(
            "🎨 FLUX is generating brochure image..."
        ):

            image_path = generate_image(
                image_prompt,
                "generated_image.png"
            )

        st.success(
            "✅ AI image generated!"
        )

        st.image(
            image_path,
            caption="AI Generated Brochure Image",
            use_container_width=True
        )

    except Exception as e:

        st.error(
            f"❌ Image generation failed: {e}"
        )

        st.stop()


    # ========================================================
    # STEP 5 — PDF GENERATION
    # ========================================================

    st.divider()

    st.markdown("""
    <div class="step-card">
        <div class="step-header">
            <span class="step-number-badge">5</span>
            <span class="step-title">Brochure PDF</span>
            <span class="step-status">● Creating</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:

        with st.spinner(
            "📄 Creating final brochure PDF..."
        ):

            pdf_path = create_brochure_pdf(
                brochure_data=brochure_data,
                image_path=image_path,
                output_path="ai_brochure.pdf"
            )

        st.success(
            "✅ Brochure PDF created!"
        )

    except Exception as e:

        st.error(
            f"❌ PDF generation failed: {e}"
        )

        st.stop()


    # ========================================================
    # DOWNLOAD
    # ========================================================

    st.divider()

    st.markdown("""
    <div class="success-card">
        <h2>🎉 Your Brochure is Ready!</h2>
        <p>Download your professionally generated brochure</p>
    </div>
    """, unsafe_allow_html=True)


    with open(
        pdf_path,
        "rb"
    ) as pdf_file:

        st.download_button(
            label="📥 Download Brochure PDF",
            data=pdf_file,
            file_name="ai_brochure.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    st.markdown("</div>", unsafe_allow_html=True)