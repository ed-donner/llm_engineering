import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
import queue
import threading
import time
import asyncio
import gradio as gr
import httpx
import plotly.graph_objects as go
import numpy as np
from sklearn.manifold import TSNE
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available - plots will show sample data")

from shared.log_utils import reformat

class MockAgentFramework:
    """Mock agent framework to prevent NoneType errors when real framework fails to initialize"""
    def __init__(self):
        self.memory = []
    
    async def run(self):
        return []

class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

def html_for(log_data):
    output = '<br>'.join(log_data[-18:])
    return f"""
    <div id="scrollContent" style="height: 400px; overflow-y: auto; border: 1px solid #ccc; background-color: #222229; padding: 10px;">
    {output}
    </div>
    """

def setup_logging(log_queue):
    handler = QueueHandler(log_queue)
    formatter = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class App:
    def __init__(self):    
        self.agent_framework = None

    def get_agent_framework(self):
        if not self.agent_framework:
            try:
                # Add the shared directory to the path
                import sys
                import os
                shared_path = os.path.join(os.path.dirname(__file__), '..', 'shared')
                if shared_path not in sys.path:
                    sys.path.insert(0, shared_path)
                
                from deal_agent_framework_client import DealAgentFrameworkClient
                self.agent_framework = DealAgentFrameworkClient()
            except Exception as e:
                logging.error(f"Failed to initialize agent framework: {e}")
                # Create a mock framework to prevent NoneType errors
                self.agent_framework = MockAgentFramework()
        return self.agent_framework

    def table_for(self, opps):
        if not opps:
            return []
        try:
            return [[opp.deal.product_description, f"${opp.deal.price:.2f}", f"${opp.estimate:.2f}", f"${opp.discount:.2f}", opp.deal.url] for opp in opps]
        except Exception as e:
            logging.error(f"Error formatting opportunities table: {e}")
            return []

    def update_output(self, log_data, log_queue, result_queue):
        initial_result = self.table_for(self.get_agent_framework().memory)
        final_result = None
        while True:
            try:
                message = log_queue.get_nowait()
                log_data.append(reformat(message))
                yield log_data, html_for(log_data), final_result or initial_result
            except queue.Empty:
                try:
                    final_result = result_queue.get_nowait()
                    yield log_data, html_for(log_data), final_result or initial_result
                except queue.Empty:
                    if final_result is not None:
                        break
                    time.sleep(0.1)

    def get_initial_plot(self):
        fig = go.Figure()
        fig.update_layout(
            title='Loading vector DB...',
            height=400,
        )
        return fig

    def get_sample_plot(self):
        """Create a sample plot when vector database is not available"""
        fig = go.Figure()
        
        # Create some sample data points
        x = np.random.randn(50)
        y = np.random.randn(50)
        z = np.random.randn(50)
        
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(
                size=5,
                color=z,
                colorscale='Viridis',
                opacity=0.7
            ),
            name='Sample Data'
        ))
        
        fig.update_layout(
            title='Sample 3D Plot (Vector DB not available)',
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z'
            ),
            height=400,
            margin=dict(r=5, b=1, l=5, t=2)
        )
        return fig

    def get_plot(self):
        if not CHROMADB_AVAILABLE:
            logging.warning("ChromaDB not available - showing sample plot")
            return self.get_sample_plot()
            
        try:
            client = chromadb.PersistentClient(path='data/vectorstore')
            collections = client.list_collections()
            
            if not collections:
                logging.warning("No collections found in vectorstore - creating sample plot")
                return self.get_sample_plot()
            
            collection = client.get_collection('products')
            count = collection.count()
            
            if count == 0:
                logging.warning("Products collection is empty - creating sample plot")
                return self.get_sample_plot()
            
            result = collection.get(include=['embeddings', 'documents', 'metadatas'], limit=1000)
            vectors = np.array(result['embeddings'])
            documents = result['documents']
            categories = [metadata['category'] for metadata in result['metadatas']]
            
            CATEGORIES = ['Appliances', 'Automotive', 'Cell_Phones_and_Accessories', 'Electronics','Musical_Instruments', 'Office_Products', 'Tools_and_Home_Improvement', 'Toys_and_Games']
            COLORS = ['red', 'blue', 'brown', 'orange', 'yellow', 'green' , 'purple', 'cyan']
            colors = [COLORS[CATEGORIES.index(c)] if c in CATEGORIES else 'gray' for c in categories]
            
            tsne = TSNE(n_components=3, random_state=42, n_jobs=-1)
            reduced_vectors = tsne.fit_transform(vectors)
            
            fig = go.Figure(data=[go.Scatter3d(
                x=reduced_vectors[:, 0],
                y=reduced_vectors[:, 1],
                z=reduced_vectors[:, 2],
                mode='markers',
                marker=dict(size=2, color=colors, opacity=0.7),
            )])
            
            fig.update_layout(
                scene=dict(xaxis_title='x', 
                           yaxis_title='y', 
                           zaxis_title='z',
                           aspectmode='manual',
                           aspectratio=dict(x=2.2, y=2.2, z=1),
                           camera=dict(
                               eye=dict(x=1.6, y=1.6, z=0.8)
                           )),
                height=400,
                margin=dict(r=5, b=1, l=5, t=2)
            )
            return fig
        except Exception as e:
            logging.error(f"Error creating plot: {e}")
            return self.get_sample_plot()

    def do_run(self):
        if not self.agent_framework:
            logging.warning("Agent framework not available")
            return []
        
        try:
            # Use asyncio.run to handle the async call synchronously
            import asyncio
            new_opportunities = asyncio.run(self.agent_framework.run())
            table = self.table_for(new_opportunities)
            return table
        except Exception as e:
            logging.error(f"Error in do_run: {e}")
            return []

    def run_with_logging(self, initial_log_data):
        log_queue = queue.Queue()
        result_queue = queue.Queue()
        setup_logging(log_queue)
        
        def worker():
            result = self.do_run()
            result_queue.put(result)
        
        thread = threading.Thread(target=worker)
        thread.start()
        
        for log_data, output, final_result in self.update_output(initial_log_data, log_queue, result_queue):
            yield log_data, output, final_result

    def do_select(self, selected_index: gr.SelectData):
        opportunities = self.get_agent_framework().memory
        row = selected_index.index[0]
        opportunity = opportunities[row]
        # Send alert via HTTP to the notification service
        try:
            import httpx
            import asyncio
            # Convert opportunity to the format expected by notification service
            alert_data = {
                "deal": opportunity.deal.model_dump(),
                "estimate": opportunity.estimate,
                "discount": opportunity.discount
            }
            asyncio.run(httpx.post("http://localhost:8007/alert", json=alert_data))
        except Exception as e:
            logging.error(f"Failed to send alert: {e}")

    def run(self):
        with gr.Blocks(title="The Price is Right", fill_width=True) as ui:
            
            log_data = gr.State([])
            
            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:24px"><strong>The Price is Right</strong> - Autonomous Agent Framework that hunts for deals</div>')
            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:14px">A proprietary fine-tuned LLM deployed on Modal and a RAG pipeline with a frontier model collaborate to send push notifications with great online deals.</div>')
            with gr.Row():
                opportunities_dataframe = gr.Dataframe(
                    headers=["Deals found so far", "Price", "Estimate", "Discount", "URL"],
                    wrap=True,
                    column_widths=[6, 1, 1, 1, 3],
                    row_count=10,
                    col_count=5,
                    max_height=400,
                )
            with gr.Row():
                with gr.Column(scale=1):
                    logs = gr.HTML()
                with gr.Column(scale=1):
                    plot = gr.Plot(value=self.get_plot(), show_label=False)
        
            ui.load(self.run_with_logging, inputs=[log_data], outputs=[log_data, logs, opportunities_dataframe])

            timer = gr.Timer(value=300, active=True)
            timer.tick(self.run_with_logging, inputs=[log_data], outputs=[log_data, logs, opportunities_dataframe])

            opportunities_dataframe.select(self.do_select)
        
        # Try to launch on port 7860, fallback to other ports if needed
        ports_to_try = [7860, 7861, 7862, 7863, 7864]
        for port in ports_to_try:
            try:
                ui.launch(share=False, inbrowser=True, server_name="0.0.0.0", server_port=port)
                break
            except OSError as e:
                if "address already in use" in str(e) and port < ports_to_try[-1]:
                    logging.warning(f"Port {port} is already in use, trying next port...")
                    continue
                else:
                    raise e

if __name__=="__main__":
    import asyncio
    App().run()
