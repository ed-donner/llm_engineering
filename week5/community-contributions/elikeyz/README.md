# Tailored Cover Letter Generation with LLMs

This repository contains a Python script that demonstrates how to ingest a resume PDF, extract relevant information, and generate a tailored cover letter using a Large Language Model (LLM). The script uses the PyPDF2 library for PDF parsing and Pydantic for data validation.

## Requirements

- Python 3.8 or higher
- PyPDF2
- Pydantic
You can install the required libraries using pip:

```bash
uv pip install -r requirements.txt
```

## Usage

1. Place your resume PDF in the specified path (`pdf_file` variable in the script).
2. Run the ingest-resume.py script to extract information from the resume and populate your vector database.
3. Run the generate-resume.py script to open the Gradio UI to generate a tailored cover letter.
4. Follow the prompts in the Gradio UI to input the job description and then, click the Generate Cover Letter button.
5. The generated cover letter will be displayed in the UI, and you can copy it for your job applications.

## Notes

- Ensure that the paths specified in the script are correct and that you have the necessary permissions to read the PDF and write to the output files.
- The script is designed to be modular, allowing for easy modifications and extensions, such as adding support for different resume formats or integrating with other LLM providers.
- The generated cover letter is based on the information extracted from the resume and the job description provided, so make sure to provide accurate and relevant information for the best results.
- This project is a demonstration of how to leverage LLMs for personalized content generation and can be further enhanced with additional features such as multiple resume formats, more sophisticated parsing techniques, and integration with job application platforms.
