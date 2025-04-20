# src/llm/helper/prompt_utils.py

"""
Prompt management utilities for the Website Summary Tool
"""

from structures.models import Website

# Default prompts
DEFAULT_SYSTEM_PROMPT = ("You are an assistant that analyzes the contents of a website "
                "and provides a short summary, ignoring text that might be navigation related. "
                "Respond in markdown.")

DEFAULT_USER_PROMPT_TEMPLATE = """
You are looking at a website titled {title}
The contents of this website is as follows; 
please provide a short summary of this website in markdown.
If it includes news or announcements, then summarize these too.

{text}
"""

class PromptManager:
    """Class to manage prompts for LLM interactions."""
    
    def __init__(self, system_prompt=None, user_prompt_template=None):
        """
        Initialize a PromptManager with customizable prompts.
        
        Args:
            system_prompt: Custom system prompt (uses default if None)
            user_prompt_template: Custom user prompt template (uses default if None)
        """
        self.system_prompt = system_prompt if system_prompt is not None else DEFAULT_SYSTEM_PROMPT
        self.user_prompt_template = user_prompt_template if user_prompt_template is not None else DEFAULT_USER_PROMPT_TEMPLATE
    
    def create_user_prompt(self, website):
        """
        Create a user prompt that includes website information.
        
        Args:
            website: A Website object containing parsed content
            
        Returns:
            str: The formatted user prompt
        """
        return self.user_prompt_template.format(title=website.title, text=website.text)
    
    def create_messages(self, website):
        """
        Create the messages array for the LLM API call.
        
        Args:
            website: A Website object containing parsed content
            
        Returns:
            list: The messages list for the API call
        """
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.create_user_prompt(website)}
        ]