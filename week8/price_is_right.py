import gradio as gr
from deal_agent_framework import DealAgentFramework
from agents.deals import Opportunity, Deal

class App:

    def __init__(self):    
        self.agent_framework = None

    def run(self):
        with gr.Blocks(title="El Precio Justo", fill_width=True) as ui:
        
            def table_for(opps):
                return [[opp.deal.product_description, f"${opp.deal.price:.2f}", f"${opp.estimate:.2f}", f"${opp.discount:.2f}", opp.deal.url] for opp in opps]
        
            def start():
                self.agent_framework = DealAgentFramework()
                opportunities = self.agent_framework.memory
                table = table_for(opportunities)
                return table
        
            def go():
                self.agent_framework.run()
                new_opportunities = self.agent_framework.memory
                table = table_for(new_opportunities)
                return table
        
            def do_select(selected_index: gr.SelectData):
                opportunities = self.agent_framework.memory
                row = selected_index.index[0]
                opportunity = opportunities[row]
                self.agent_framework.planner.messenger.alert(opportunity)
        
            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:24px">El precio justo: agencia de búsqueda de ofertas con IA</div>')
            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:14px">Marco de agente autónomo que encuentra ofertas en línea, colaborando con un LLM patentado y optimizado implementado en Modal, y un pipeline RAG con un modelo de frontera y Chroma.</div>')
            with gr.Row():
                gr.Markdown('<div style="text-align: center;font-size:14px">Ofertas encontradas hasta el momento:</div>')
            with gr.Row():
                opportunities_dataframe = gr.Dataframe(
                    headers=["Descripción", "Precio", "Estimación", "Descuento", "URL"],
                    wrap=True,
                    column_widths=[4, 1, 1, 1, 2],
                    row_count=10,
                    col_count=5,
                    max_height=400,
                )
        
            ui.load(start, inputs=[], outputs=[opportunities_dataframe])

            timer = gr.Timer(value=60)
            timer.tick(go, inputs=[], outputs=[opportunities_dataframe])

            opportunities_dataframe.select(do_select)
        
        ui.launch(share=False, inbrowser=True)

if __name__=="__main__":
    App().run()
    