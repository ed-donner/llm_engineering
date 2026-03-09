"""
Gradio Web UI for Advanced Price Predictor
"""

import gradio as gr
import numpy as np
import pandas as pd
import pickle
import sys
sys.path.append('.')

from src.items import Item
from src.models import XGBoostPricer, NeuralNetPricer
from src.rag import RAGSystem
from src.embeddings import EmbeddingGenerator

# Global variables for loaded models
xgb_model = None
nn_model = None
rag_system = None
embedding_gen = None
train_items = None


def load_models():
    """Load all trained models"""
    global xgb_model, nn_model, rag_system, embedding_gen, train_items
    
    try:
        # Load XGBoost
        xgb_model = XGBoostPricer()
        xgb_model.load('data/models/xgboost_model.pkl')
        
        # Load Neural Network
        nn_model = NeuralNetPricer(embedding_dim=384, feature_dim=12)
        nn_model.load('data/models/neural_net_model.pth')
        
        # Load RAG system
        with open('data/rag_system.pkl', 'rb') as f:
            rag_system = pickle.load(f)
        
        # Load embedding generator
        embedding_gen = EmbeddingGenerator()
        
        # Load training items for RAG
        with open('data/train_items_rag.pkl', 'rb') as f:
            train_items = pickle.load(f)
        
        return "✅ All models loaded successfully!"
    except Exception as e:
        return f"❌ Error loading models: {str(e)}\n\nPlease run the training notebooks first!"


def predict_price(title, category, description, weight=None, brand=None):
    """
    Predict price for a product
    
    Args:
        title: Product title
        category: Product category
        description: Product description
        weight: Product weight (optional)
        brand: Product brand (optional)
    """
    if xgb_model is None:
        return "Please load models first!", None, None, None, None
    
    try:
        # Create item
        item = Item(
            title=title,
            category=category,
            price=0,  # Unknown
            summary=description,
            weight=weight if weight else 0
        )
        
        # Enhance item
        item.enhance()
        if brand:
            item.brand = brand
        
        # Generate embedding
        embedding = embedding_gen.embed_text(description)
        
        # Get RAG features
        similar = rag_system.search(embedding, k=10)
        stats = rag_system.get_price_statistics(similar)
        item.rag_mean_price = stats['mean']
        item.rag_median_price = stats['median']
        item.rag_std_price = stats['std']
        item.rag_weighted_price = rag_system.get_weighted_price(similar)
        
        # Get features
        features = pd.DataFrame([{
            **item.get_feature_dict(),
            'rag_mean_price': item.rag_mean_price,
            'rag_median_price': item.rag_median_price,
            'rag_std_price': item.rag_std_price,
            'rag_weighted_price': item.rag_weighted_price
        }])
        
        # Predictions
        xgb_pred = float(xgb_model.predict(features)[0])
        nn_pred = float(nn_model.predict(embedding.reshape(1, -1), features)[0])
        rag_pred = float(item.rag_mean_price)
        
        # Ensemble (weighted average)
        ensemble_pred = 0.4 * xgb_pred + 0.4 * nn_pred + 0.2 * rag_pred
        
        # Similar products info
        similar_info = "Similar Products:\n\n"
        for i, prod in enumerate(similar[:5], 1):
            similar_info += f"{i}. {prod.title[:50]}... - ${prod.price:.2f}\n"
        
        return (
            f"${ensemble_pred:.2f}",
            f"${xgb_pred:.2f}",
            f"${nn_pred:.2f}",
            f"${rag_pred:.2f}",
            similar_info
        )
    
    except Exception as e:
        return f"Error: {str(e)}", None, None, None, None


def create_ui():
    """Create Gradio interface"""
    
    with gr.Blocks(title="Advanced Price Predictor", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎯 Advanced Price Predictor v2.0
        
        Predict product prices using ensemble ML models (XGBoost + Neural Network + RAG)
        """)
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Load Models")
                load_btn = gr.Button("🔄 Load Models", variant="primary")
                load_status = gr.Textbox(label="Status", interactive=False)
        
        gr.Markdown("---")
        
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Product Information")
                
                title_input = gr.Textbox(
                    label="Product Title",
                    placeholder="e.g., Samsung 55-inch 4K Smart TV",
                    lines=2
                )
                
                category_input = gr.Dropdown(
                    label="Category",
                    choices=[
                        "Electronics",
                        "Appliances",
                        "Tools_and_Home_Improvement",
                        "Automotive",
                        "Office_Products",
                        "Cell_Phones_and_Accessories",
                        "Toys_and_Games",
                        "Musical_Instruments"
                    ],
                    value="Electronics"
                )
                
                description_input = gr.Textbox(
                    label="Product Description",
                    placeholder="Enter detailed product description...",
                    lines=5
                )
                
                with gr.Row():
                    weight_input = gr.Number(
                        label="Weight (oz) - Optional",
                        value=None,
                        minimum=0
                    )
                    brand_input = gr.Textbox(
                        label="Brand - Optional",
                        placeholder="e.g., Samsung"
                    )
                
                predict_btn = gr.Button("💰 Predict Price", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                gr.Markdown("### Predictions")
                
                ensemble_output = gr.Textbox(
                    label="🎯 Ensemble Prediction (Final)",
                    interactive=False,
                    elem_classes=["highlight"]
                )
                
                gr.Markdown("#### Individual Models:")
                
                xgb_output = gr.Textbox(
                    label="XGBoost",
                    interactive=False
                )
                
                nn_output = gr.Textbox(
                    label="Neural Network",
                    interactive=False
                )
                
                rag_output = gr.Textbox(
                    label="RAG Baseline",
                    interactive=False
                )
                
                similar_output = gr.Textbox(
                    label="Similar Products",
                    interactive=False,
                    lines=6
                )
        
        gr.Markdown("---")
        
        with gr.Row():
            gr.Markdown("""
            ### 📊 Model Information
            
            - **Ensemble**: Weighted combination of all models (40% XGBoost + 40% Neural Net + 20% RAG)
            - **XGBoost**: Gradient boosting with engineered features
            - **Neural Network**: Deep learning with text embeddings
            - **RAG**: Retrieval-Augmented Generation using similar products
            
            **Expected Accuracy**: MAE ~$28-35 (40-50% better than baseline)
            """)
        
        # Examples
        gr.Examples(
            examples=[
                [
                    "Samsung 55-inch 4K UHD Smart LED TV",
                    "Electronics",
                    "Title: Samsung 55-inch 4K Smart TV\nCategory: Electronics\nBrand: Samsung\nDescription: 4K UHD resolution, Smart TV features, LED display\nDetails: 55-inch screen, HDR support, built-in streaming apps",
                    320,
                    "Samsung"
                ],
                [
                    "KitchenAid Stand Mixer",
                    "Appliances",
                    "Title: KitchenAid Professional Stand Mixer\nCategory: Appliances\nBrand: KitchenAid\nDescription: Professional-grade stand mixer for baking\nDetails: 5-quart capacity, 10-speed settings, includes attachments",
                    240,
                    "KitchenAid"
                ],
                [
                    "Dewalt Cordless Drill Set",
                    "Tools_and_Home_Improvement",
                    "Title: Dewalt 20V MAX Cordless Drill Combo Kit\nCategory: Tools\nBrand: Dewalt\nDescription: Professional cordless drill with battery and charger\nDetails: 20V battery, variable speed, LED light, carrying case",
                    180,
                    "Dewalt"
                ]
            ],
            inputs=[title_input, category_input, description_input, weight_input, brand_input],
            label="Try these examples:"
        )
        
        # Event handlers
        load_btn.click(
            fn=load_models,
            outputs=load_status
        )
        
        predict_btn.click(
            fn=predict_price,
            inputs=[title_input, category_input, description_input, weight_input, brand_input],
            outputs=[ensemble_output, xgb_output, nn_output, rag_output, similar_output]
        )
    
    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
