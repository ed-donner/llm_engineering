"""
Application module for LLM prompts and Gradio chat interface.
Consolidates prompt_engine and chat_interface functionality.
"""

import os
import re
from datetime import datetime

import gradio as gr
import openai
from dotenv import load_dotenv

from config import LLM_MODEL

load_dotenv()


class RecipeApp:
    """Recipe assistant with LLM integration and Gradio UI."""
    
    SYSTEM_PROMPT = "You are a helpful cooking assistant and recipe expert."
    
    COMMON_INGREDIENTS = [
        'chicken', 'beef', 'pork', 'fish', 'tofu', 'eggs',
        'rice', 'pasta', 'bread', 'potato', 'onion', 'garlic',
        'tomato', 'cheese', 'milk', 'butter', 'oil', 'salt',
        'pepper', 'carrot', 'broccoli', 'spinach', 'mushroom'
    ]
    
    def __init__(self, rag_engine, api_key=None):
        self.rag = rag_engine
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = LLM_MODEL
        self.chat_history = []
    
    def _generate_stream(self, prompt, max_tokens=500, temperature=0.7):
        """Generate streaming response from LLM."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}. Please check your OpenAI API key."
    
    def _create_recommendation_prompt(self, search_results, user_query):
        """Create prompt for recipe recommendations."""
        recipes_context = ""
        for i, result in enumerate(search_results[:3]):
            recipe = result['recipe']
            recipes_context += f"""
Recipe {i+1}: {recipe['title']}
Ingredients: {', '.join(recipe['ingredients'][:8])}...
Instructions: {recipe['instructions'][:200]}...
Prep Time: {recipe.get('prep_time', 'Unknown')} min | Cook Time: {recipe.get('cook_time', 'Unknown')} min
Cuisine: {recipe.get('cuisine', 'Unknown')} | Vegetarian: {recipe.get('dietary_info', {}).get('vegetarian', False)}
"""
        
        return f"""A user is asking: "{user_query}"

Based on these recipes from our database:
{recipes_context}

Provide a helpful response:
- Recommend the most suitable recipe(s)
- Explain why you chose them
- Offer cooking tips or substitutions if relevant
Keep it conversational and practical."""
    
    def _create_cooking_prompt(self, recipe, user_question):
        """Create prompt for cooking assistance."""
        return f"""You are helping someone cook this recipe:

Recipe: {recipe['title']}
Ingredients: {', '.join(recipe['ingredients'])}
Instructions: {recipe['instructions']}
Prep Time: {recipe.get('prep_time', 'Unknown')} min | Cook Time: {recipe.get('cook_time', 'Unknown')} min

User asks: "{user_question}"

Provide step-by-step guidance with techniques, visual cues, and tips to avoid common mistakes."""
    
    def _extract_ingredients(self, text):
        """Extract ingredients from user text."""
        text_lower = text.lower()
        return [ing for ing in self.COMMON_INGREDIENTS if ing in text_lower]
    
    def _generate_response(self, message):
        """Route message to appropriate handler."""
        msg_lower = message.lower()
        
        if any(word in msg_lower for word in ['ingredient', 'have', 'using', 'with']):
            yield from self._handle_ingredient_query(message)
        elif any(word in msg_lower for word in ['quick', 'fast', 'minutes', 'time']):
            yield from self._handle_time_query(message)
        elif any(word in msg_lower for word in ['vegetarian', 'vegan', 'gluten-free', 'healthy']):
            yield from self._handle_dietary_query(message)
        elif any(word in msg_lower for word in ['how to', 'cook', 'prepare', 'make']):
            yield from self._handle_cooking_query(message)
        else:
            yield from self._handle_general_query(message)
    
    def _handle_ingredient_query(self, message):
        """Handle ingredient-based queries."""
        ingredients = self._extract_ingredients(message)
        
        if ingredients:
            results = self.rag.search_by_ingredients(ingredients, max_results=3)
            if results:
                prompt = self._create_recommendation_prompt(results, message)
                yield from self._generate_stream(prompt)
            else:
                yield f"No recipes found with {', '.join(ingredients)}. Try different ingredients!"
        else:
            yield "Which ingredients would you like to use? Example: 'What can I make with chicken and rice?'"
    
    def _handle_time_query(self, message):
        """Handle time-constraint queries."""
        time_match = re.search(r'(\d+)\s*min', message)
        max_time = int(time_match.group(1)) if time_match else 30
        
        results = self.rag.search_by_time(max_prep_time=max_time, max_results=3)
        if results:
            prompt = self._create_recommendation_prompt(results, message)
            yield from self._generate_stream(prompt)
        else:
            yield f"No recipes found under {max_time} minutes. Try increasing the time!"
    
    def _handle_dietary_query(self, message):
        """Handle dietary restriction queries."""
        restrictions = []
        msg_lower = message.lower()
        
        if 'vegetarian' in msg_lower:
            restrictions.append('vegetarian')
        if 'vegan' in msg_lower:
            restrictions.append('vegan')
        if 'gluten-free' in msg_lower or 'gluten free' in msg_lower:
            restrictions.append('gluten_free')
        
        results = self.rag.search_natural_language(message, max_results=3)
        
        if restrictions:
            results = [r for r in results if any(
                r['recipe'].get('dietary_info', {}).get(rest, False) for rest in restrictions
            )]
        
        if results:
            prompt = self._create_recommendation_prompt(results, message)
            yield from self._generate_stream(prompt)
        else:
            yield "No recipes found matching your dietary requirements. Try a broader search!"
    
    def _handle_cooking_query(self, message):
        """Handle cooking technique questions."""
        results = self.rag.search_natural_language(message, max_results=1)
        
        if results:
            prompt = self._create_cooking_prompt(results[0]['recipe'], message)
            yield from self._generate_stream(prompt)
        else:
            yield "I'd be happy to help! Could you be more specific about what you'd like to cook?"
    
    def _handle_general_query(self, message):
        """Handle general recipe queries."""
        results = self.rag.search_natural_language(message, max_results=3)
        
        if results:
            prompt = self._create_recommendation_prompt(results, message)
            yield from self._generate_stream(prompt)
        else:
            yield "No recipes found. Try being more specific about ingredients, cuisine, or cooking method!"
    
    def process_message(self, message, history):
        """Process chat message and stream response."""
        history = history or []
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": ""})
        
        yield history, ""
        
        try:
            accumulated = ""
            for token in self._generate_response(message):
                accumulated += token
                history[-1]["content"] = accumulated
                yield history, ""
        except Exception as e:
            history[-1]["content"] = f"Error: {str(e)}"
            yield history, ""
    
    def create_interface(self):
        """Create Gradio chat interface."""
        stats = self.rag.get_stats()
        
        with gr.Blocks(title="Recipe RAG Assistant") as interface:
            gr.Markdown("""
# Recipe RAG Assistant

I can help you find recipes based on ingredients, time constraints, or dietary needs.

**Try asking:**
- "What can I make with chicken and pasta?"
- "I need a quick dinner under 30 minutes"
- "Show me healthy vegetarian recipes"
- "How do I properly cook rice?"
            """)
            
            chatbot = gr.Chatbot(height=450)
            
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Ask about recipes...",
                    label="Your message",
                    scale=4
                )
                send_btn = gr.Button("Send", scale=1, variant="primary")
            
            gr.Examples(
                examples=[
                    "What can I make with chicken and rice?",
                    "Quick dinner recipe under 30 minutes",
                    "Healthy vegetarian recipes",
                    "How do I cook perfect pasta?"
                ],
                inputs=msg
            )
            
            gr.Markdown(f"""
**Database:** {stats['total_recipes']} recipes | {stats['total_chunks']} chunks | Updated: {datetime.now().strftime('%Y-%m-%d')}
            """)
            
            msg.submit(self.process_message, [msg, chatbot], [chatbot, msg])
            send_btn.click(self.process_message, [msg, chatbot], [chatbot, msg])
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        interface = self.create_interface()
        interface.launch(**kwargs)
