from openai import OpenAI
from interfaces.ai_client import AIClient

class OpenRouterClient(AIClient):
    def __init__(self, api_key, model):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        
    def chat(self, messages):
        print(f"[OpenRouter] Calling {self.model}")
        print(f"[OpenRouter] Messages count: {len(messages)}")
        
        # Calculate input tokens estimate (rough)
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        estimated_tokens = total_chars // 4  # Rough estimate
        print(f"[OpenRouter] Estimated input tokens: {estimated_tokens}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                extra_body={
                    "usage": {
                        "include": True
                    }
                }
            )
            
            content = response.choices[0].message.content
            print(f"[OpenRouter] Response length: {len(content)} chars")
            print(f"[OpenRouter] Response preview: {content[:100]}...")
            
            # Print usage information if available
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                print(f"[OpenRouter] Token usage:")
                print(f"  - Prompt tokens: {usage.prompt_tokens}")
                print(f"  - Completion tokens: {usage.completion_tokens}")
                print(f"  - Total tokens: {usage.total_tokens}")
                
                # Try to get cost information
                if hasattr(usage, 'cost') and usage.cost:
                    print(f"  - Cost: ${usage.cost:.6f}")
                else:
                    # Rough cost estimate for GPT-4o-mini ($0.15/1M input, $0.60/1M output)
                    estimated_cost = (usage.prompt_tokens * 0.15 + usage.completion_tokens * 0.60) / 1_000_000
                    print(f"  - Estimated cost: ${estimated_cost:.6f}")
            
            print(f"[OpenRouter] Success")
            return content
            
        except Exception as e:
            print(f"[OpenRouter] Error: {str(e)}")
            return f"Error: {str(e)}"
    
    def analyze_code(self, code, language):
        print(f"[OpenRouter] Code analysis request - Language: {language}")
        print(f"[OpenRouter] Code length: {len(code)} chars, {len(code.splitlines())} lines")
        
        prompt = f"Analyze this {language} code for bugs and improvements:\n\n```{language}\n{code}\n```"
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages)
    
    def generate_linkedin_post(self, topic, tone="professional"):
        print(f"[OpenRouter] LinkedIn post request - Topic: {topic[:50]}...")
        print(f"[OpenRouter] Tone: {tone}")
        
        tone_styles = {
            "professional": "formal, informative, and industry-focused",
            "casual": "friendly, approachable, and conversational",
            "inspirational": "motivating, uplifting, and thought-provoking",
            "educational": "informative, teaching-focused, and valuable"
        }
        
        style = tone_styles.get(tone, "professional and engaging")
        
        prompt = f"""Create a LinkedIn post about: {topic}

Make it {style}. Include:
- Hook that grabs attention
- 2-3 key insights or takeaways  
- Call to action or question for engagement
- Relevant hashtags (3-5)

Keep it under 300 words and format for LinkedIn readability."""

        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages)