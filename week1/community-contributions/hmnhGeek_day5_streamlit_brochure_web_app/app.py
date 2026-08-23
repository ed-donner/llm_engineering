import os
import tempfile

import streamlit as st
from markdown_pdf import MarkdownPdf, Section

from services.model_service import ModelService


st.set_page_config(
    page_title="AI Brochure Generator",
    page_icon="📄",
    layout="wide"
)


@st.cache_resource
def get_model_service():
    return ModelService()


def markdown_to_pdf(company_name: str, markdown_text: str) -> bytes:
    """
    Convert markdown to PDF bytes.
    """

    clean_markdown = markdown_text.strip()

    # Ensure the document starts with a level-1 heading.
    # This prevents markdown-pdf hierarchy issues.
    if not clean_markdown.startswith("# "):
        clean_markdown = f"# {company_name}\n\n{clean_markdown}"

    pdf = MarkdownPdf()

    pdf.add_section(
        Section(clean_markdown)
    )

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    ) as temp_file:
        pdf_path = temp_file.name

    try:
        pdf.save(pdf_path)

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        return pdf_bytes

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


def main():

    st.title("📄 AI Brochure Generator")

    st.markdown(
        """
        Generate a professional brochure by analyzing a company's
        website and relevant pages.
        """
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g. OpenAI"
        )

    with col2:
        website_url = st.text_input(
            "Company Website",
            placeholder="https://openai.com"
        )

    st.divider()

    if st.button(
        "Generate Brochure",
        type="primary",
        use_container_width=True
    ):

        if not company_name.strip():
            st.error("Please enter a company name.")
            return

        if not website_url.strip():
            st.error("Please enter a company website URL.")
            return

        try:

            model_service = get_model_service()

            with st.spinner(
                "Analyzing website, collecting information, and generating brochure..."
            ):

                brochure_markdown = model_service.get_brochure_markdown(
                    company_name,
                    website_url
                )

            st.success("Brochure generated successfully!")

            st.subheader("Generated Brochure")

            st.markdown(brochure_markdown)

            with st.spinner("Preparing PDF..."):

                pdf_bytes = markdown_to_pdf(
                    company_name,
                    brochure_markdown
                )

            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=f"{company_name.lower().replace(' ', '_')}_brochure.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        except Exception as ex:
            st.error(f"Failed to generate brochure: {str(ex)}")


if __name__ == "__main__":
    main()
