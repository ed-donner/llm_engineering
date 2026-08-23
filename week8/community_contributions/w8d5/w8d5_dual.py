import os
import sys
import logging
import queue
import threading
import time
import gradio as gr
import plotly.graph_objects as go

w8d5_path = os.path.abspath(os.path.dirname(__file__))
week8_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if w8d5_path not in sys.path:
    sys.path.insert(0, w8d5_path)
if week8_path not in sys.path:
    sys.path.insert(0, week8_path)

from log_utils import reformat
from helpers.travel_dual_framework import TravelDualFramework
from helpers.travel_deals import TravelOpportunity, TravelDeal


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))


log_queue = queue.Queue()
queue_handler = QueueHandler(log_queue)
queue_handler.setFormatter(
    logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
)
logging.getLogger().addHandler(queue_handler)
logging.getLogger().setLevel(logging.INFO)

agent_framework = TravelDualFramework()
agent_framework.init_agents_as_needed()

CHECK_INTERVAL = 300


def run_agent_framework():
    while True:
        try:
            agent_framework.run()
        except Exception as e:
            logging.error(f"Error in agent framework: {e}")
        time.sleep(CHECK_INTERVAL)


framework_thread = threading.Thread(target=run_agent_framework, daemon=True)
framework_thread.start()


def get_llm_table(llm_opps):
    return [[
        opp.deal.destination,
        opp.deal.deal_type,
        f"${opp.deal.price:.2f}",
        f"${opp.estimate:.2f}",
        f"${opp.discount:.2f}",
        opp.deal.url[:50] + "..." if len(opp.deal.url) > 50 else opp.deal.url
    ] for opp in llm_opps]


def get_xgb_table(xgb_opps):
    return [[
        opp.deal.destination,
        opp.deal.deal_type,
        f"${opp.deal.price:.2f}",
        f"${opp.estimate:.2f}",
        f"${opp.discount:.2f}",
        opp.deal.url[:50] + "..." if len(opp.deal.url) > 50 else opp.deal.url
    ] for opp in xgb_opps]


log_data = []

def update_ui():
    global log_data
    llm_data = get_llm_table(agent_framework.llm_memory)
    xgb_data = get_xgb_table(agent_framework.xgb_memory)
    
    while not log_queue.empty():
        try:
            message = log_queue.get_nowait()
            log_data.append(reformat(message))
        except:
            break
    
    logs_html = '<div style="height: 500px; overflow-y: auto; border: 1px solid #ccc; background-color: #1a1a1a; padding: 10px; font-family: monospace; font-size: 12px; color: #fff;">'
    logs_html += '<br>'.join(log_data[-50:])
    logs_html += '</div>'
    
    llm_count = len(agent_framework.llm_memory)
    xgb_count = len(agent_framework.xgb_memory)
    
    stats = f"LLM Opportunities: {llm_count} | XGBoost Opportunities: {xgb_count}"
    
    return llm_data, xgb_data, logs_html, stats


def create_3d_plot():
    try:
        documents, vectors, colors, categories = TravelDualFramework.get_plot_data(max_datapoints=5000)
        
        if len(vectors) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available yet. Vectorstore will load after initialization.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        fig = go.Figure()
        
        unique_categories = list(set(categories))
        category_colors = {cat: colors[categories.index(cat)] for cat in unique_categories}
        
        for category in unique_categories:
            mask = [cat == category for cat in categories]
            cat_vectors = vectors[mask]
            
            fig.add_trace(go.Scatter3d(
                x=cat_vectors[:, 0],
                y=cat_vectors[:, 1],
                z=cat_vectors[:, 2],
                mode='markers',
                marker=dict(
                    size=3,
                    color=category_colors[category],
                    opacity=0.6
                ),
                name=category.replace('_', ' '),
                hovertemplate='<b>%{text}</b><extra></extra>',
                text=[category] * len(cat_vectors)
            ))
        
        fig.update_layout(
            title={
                'text': f'3D Travel Vectorstore Visualization ({len(vectors):,} deals)',
                'x': 0.5,
                'xanchor': 'center'
            },
            scene=dict(
                xaxis_title='Dimension 1',
                yaxis_title='Dimension 2',
                zaxis_title='Dimension 3',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=1200,
            height=600,
            margin=dict(r=0, b=0, l=0, t=40),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    except Exception as e:
        logging.error(f"Error creating 3D plot: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading plot: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="red")
        )
        return fig


with gr.Blocks(title="Travel Deal Hunter - Dual Estimation", fill_width=True, theme=gr.themes.Soft()) as ui:
    
    gr.Markdown(
        """
        <div style="text-align: center;">
            <h1 style="margin-bottom: 10px;">Travel Deal Hunter - Dual Estimation System</h1>
            <p style="color: #666; font-size: 16px;">
                Comparing LLM-based Semantic Estimation vs XGBoost Machine Learning
            </p>
            <p style="color: #999; font-size: 14px; margin-top: 10px;">
                System scans RSS feeds every 5 minutes. Use the button below to trigger a manual scan.
            </p>
        </div>
        """
    )
    
    with gr.Row():
        with gr.Column(scale=3):
            stats_display = gr.Textbox(
                label="",
                value="LLM Opportunities: 0 | XGBoost Opportunities: 0",
                interactive=False,
                show_label=False,
                container=False
            )
        with gr.Column(scale=1):
            scan_button = gr.Button("Scan Now", variant="primary")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### LLM Estimates")
            llm_dataframe = gr.Dataframe(
                headers=["Destination", "Type", "Price", "LLM Est.", "Savings", "URL"],
                datatype=["str", "str", "str", "str", "str", "str"],
                wrap=True,
                column_widths=[2, 1, 1, 1, 1, 2],
                row_count=5,
                col_count=6,
                interactive=False
            )
        
        with gr.Column(scale=1):
            gr.Markdown("### XGBoost Estimates")
            xgb_dataframe = gr.Dataframe(
                headers=["Destination", "Type", "Price", "XGB Est.", "Savings", "URL"],
                datatype=["str", "str", "str", "str", "str", "str"],
                wrap=True,
                column_widths=[2, 1, 1, 1, 1, 2],
                row_count=5,
                col_count=6,
                interactive=False
            )
    
    with gr.Row():
        with gr.Column(scale=2):
            plot_output = gr.Plot(label="3D Travel Vectorstore Visualization")
        
        with gr.Column(scale=1):
            gr.Markdown("### Agent Activity Logs")
            log_output = gr.HTML(
                value='<div style="height: 500px; overflow-y: auto; border: 1px solid #ccc; background-color: #1a1a1a; padding: 10px; font-family: monospace; font-size: 12px; color: #fff;"></div>'
            )
    
    ui.load(
        fn=lambda: (
            get_llm_table(agent_framework.llm_memory),
            get_xgb_table(agent_framework.xgb_memory),
            "",
            f"LLM Opportunities: {len(agent_framework.llm_memory)} | XGBoost Opportunities: {len(agent_framework.xgb_memory)}",
            create_3d_plot()
        ),
        outputs=[llm_dataframe, xgb_dataframe, log_output, stats_display, plot_output]
    )
    
    # Manual scan button
    def manual_scan():
        try:
            agent_framework.run()
            return update_ui()
        except Exception as e:
            logging.error(f"Manual scan error: {e}")
            return update_ui()
    
    scan_button.click(
        fn=manual_scan,
        outputs=[llm_dataframe, xgb_dataframe, log_output, stats_display]
    )
    
    # Click handlers for notifications
    def llm_click_handler(selected_index: gr.SelectData):
        try:
            row = selected_index.index[0]
            if row < len(agent_framework.llm_memory):
                opportunity = agent_framework.llm_memory[row]
                agent_framework.messenger.alert(opportunity)
                logging.info(f"Manual alert sent for LLM opportunity: {opportunity.deal.destination}")
        except Exception as e:
            logging.error(f"Error sending LLM notification: {e}")
    
    def xgb_click_handler(selected_index: gr.SelectData):
        try:
            row = selected_index.index[0]
            if row < len(agent_framework.xgb_memory):
                opportunity = agent_framework.xgb_memory[row]
                agent_framework.messenger.alert(opportunity)
                logging.info(f"Manual alert sent for XGBoost opportunity: {opportunity.deal.destination}")
        except Exception as e:
            logging.error(f"Error sending XGBoost notification: {e}")
    
    llm_dataframe.select(fn=llm_click_handler)
    xgb_dataframe.select(fn=xgb_click_handler)
    
    gr.Timer(5).tick(
        fn=update_ui,
        outputs=[llm_dataframe, xgb_dataframe, log_output, stats_display]
    )
    

if __name__ == "__main__":
    ui.launch(inbrowser=True, share=False)

