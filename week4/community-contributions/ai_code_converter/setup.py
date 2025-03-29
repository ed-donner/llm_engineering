from setuptools import setup, find_packages

setup(
    name="ai_code_converter",
    version="1.0.0",
    packages=find_packages(),
    package_data={
        'src.ai_code_converter': ['template.j2'],
    },
    install_requires=[
        'gradio',
        'openai',
        'anthropic',
        'google-generativeai',
        'python-dotenv',
        'jinja2',
    ],
    python_requires='>=3.10',
) 