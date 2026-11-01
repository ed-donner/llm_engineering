import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import gradio as gr
from sklearn.decomposition import PCA
import plotly.express as px
import pandas as pd
import numpy as np

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# The "Brain" - Logic
def get_embedding(text):
    response = client.embeddings.create(input=[text], model="text-embedding-3-small")
    return response.data[0].embedding

def get_token_probs(prompt):
    # Fixed: passed prompt as a string
    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1,
        logprobs=True,
        top_logprobs=5
    )
    return response.choices[0].logprobs.content[0].top_logprobs

# The Visualization
def plot_embeddings(user_input):
    words = [w.strip() for w in user_input.split(",")]
    vectors = [get_embedding(w) for w in words]
    coords = PCA(n_components=2).fit_transform(vectors)
    
    df = pd.DataFrame(coords, columns=['x', 'y'])
    df['word'] = words
    fig = px.scatter(df, x='x', y='y', text='word')
    fig.update_traces(mode='text', textfont_size=20)
    fig.update_layout(height=500, title="Semantic Neighborhood Map")
    return fig

def show_token_probs(prompt):
    probs = get_token_probs(prompt)
    return {p.token: np.exp(p.logprob) for p in probs}

# The Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("AI Lab: Demystifying AI")
    
    with gr.Tab("1. The Library of Meaning (Embeddings)"):
        gr.Markdown("Type words below. See how similar words cluster together in the 'Library' of AI knowledge.")
        text_input = gr.Textbox(label="Words (comma separated)", value="cat, dog, car, truck, apple, banana")
        plot_btn = gr.Button("Build the Map", variant="primary")
        plot_out = gr.Plot()
        plot_btn.click(plot_embeddings, inputs=text_input, outputs=plot_out)
        
    with gr.Tab("2. The Crossroads of Prediction (Tokens)"):
        gr.Markdown("Type a sentence. The AI calculates the probability of what comes next.")
        prompt_input = gr.Textbox(label="Type a prompt", value="The capital of Kenya is")
        pred_btn = gr.Button("Calculate Probabilities", variant="primary")
        bar_out = gr.Label(label="Next Token Choices")
        pred_btn.click(show_token_probs, inputs=prompt_input, outputs=bar_out)

demo.launch()