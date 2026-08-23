#!/usr/bin/env python3
"""
Code Explainer - Interactive Terminal Mode
Day 1 LLM Engineering Assignment
Explains code snippets using Llama 3.2 via Ollama
"""

import os
from dotenv import load_dotenv
from openai import OpenAI


class CodeExplainer:
    """Interactive code explanation assistant using Llama 3.2"""
    
    def __init__(self, model="llama3.2"):
        load_dotenv()
        
        self.client = OpenAI(
            base_url='http://localhost:11434/v1',
            api_key='ollama'
        )
        self.model = model
        
        print(f"🤖 Using Ollama with model: {self.model}")
        
        # System prompt - defines how the model should behave
        self.system_prompt = """You are an experienced programming instructor.
You analyze and explain code snippets line by line.

When explaining code:
1. Summarize the overall purpose of the code
2. Explain each important line or block
3. Highlight key programming concepts used
4. Use language that beginners can understand
5. Include practical examples when helpful

Be clear, educational, and encouraging."""
    
    def explain(self, code, stream=True):
        """Explain the given code snippet"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Explain the following code:\n\n{code}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                temperature=0.3  # Low temperature for consistent explanations
            )
            
            if stream:
                print("\n" + "="*60)
                print("📝 EXPLANATION:")
                print("="*60 + "\n")
                answer = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        print(text, end="", flush=True)
                        answer += text
                print("\n" + "="*60 + "\n")
                return answer
            else:
                result = response.choices[0].message.content
                print(f"\n📝 Explanation:\n{result}\n")
                return result
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def chat(self):
        """Start interactive chat mode"""
        print("\n" + "="*60)
        print("🎓 CODE EXPLAINER - Interactive Terminal Mode")
        print("="*60)
        print(f"Model: {self.model}")
        print(f"Provider: Ollama (Local)")
        print("\n📖 How to use:")
        print("  • Paste your code")
        print("  • Press Enter twice (empty line) when done")
        print("  • Type 'quit', 'exit', or 'q' to stop")
        print("  • Type 'clear' to start fresh")
        print("  • Type 'examples' to see sample code")
        print("="*60 + "\n")
        
        while True:
            try:
                print("📋 Paste your code below (Enter twice when done):")
                print()
                
                # Multi-line input
                lines = []
                empty_count = 0
                
                while True:
                    line = input()
                    
                    # Check for exit commands
                    if line.strip().lower() in ['quit', 'exit', 'q']:
                        print("\n👋 Thanks for using Code Explainer! Goodbye!")
                        return
                    
                    # Check for clear command
                    if line.strip().lower() == 'clear':
                        print("\n🔄 Starting fresh...\n")
                        break
                    
                    # Check for examples command
                    if line.strip().lower() == 'examples':
                        self.show_examples()
                        break
                    
                    # Empty line detection
                    if not line.strip():
                        empty_count += 1
                        if empty_count >= 1 and lines:  # One empty line is enough
                            break
                    else:
                        empty_count = 0
                        lines.append(line)
                
                # If we have code, explain it
                if lines:
                    code = "\n".join(lines)
                    self.explain(code)
                
            except KeyboardInterrupt:
                print("\n\n👋 Thanks for using Code Explainer! Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    def show_examples(self):
        """Show example code snippets"""
        print("\n" + "="*60)
        print("📚 EXAMPLE CODE SNIPPETS")
        print("="*60)
        
        examples = {
            "1. Simple Loop": """
for i in range(5):
    print(i * 2)
""",
            "2. List Comprehension": """
numbers = [1, 2, 3, 4, 5]
squares = [x**2 for x in numbers if x % 2 == 0]
print(squares)
""",
            "3. Function with Recursion": """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)

print(factorial(5))
""",
            "4. Class Definition": """
class Dog:
    def __init__(self, name):
        self.name = name
    
    def bark(self):
        return f"{self.name} says Woof!"
"""
        }
        
        for title, code in examples.items():
            print(f"\n{title}:{code}")
        
        print("="*60)
        print("💡 Copy any example above and paste it when prompted!")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    load_dotenv()
    
    print("\n🚀 Starting Code Explainer...")
    explainer = CodeExplainer()
    
    # Start interactive mode
    explainer.chat()


if __name__ == "__main__":
    main()