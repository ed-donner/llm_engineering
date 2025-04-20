#!/usr/bin/env python
# coding: utf-8

"""
Website Summary Tool
A tool to fetch website content and generate summaries using multiple LLM providers.
"""

from llm.llm_factory import LLMFactory
from helper.web_scraper import fetch_website_content
from llm.helper.prompt_utils import PromptManager
from helper.display_utils import display_summary_markdown, print_validation_result


def summarize_url(client, url, use_selenium=None, model=None, prompt_manager=None):
    """
    Fetch a website and generate a summary.
    
    Args:
        client: The LLM client
        url: The URL to summarize
        use_selenium: Whether to use Selenium for JavaScript-heavy websites.
                     If None, automatic detection is used.
        model: The model to use for generation
        prompt_manager: Optional PromptManager to customize prompts
        
    Returns:
        str: The generated summary
    """
    website = fetch_website_content(url, use_selenium)
    
    # Use default PromptManager if none provided
    if prompt_manager is None:
        prompt_manager = PromptManager()
    
    messages = prompt_manager.create_messages(website)
    
    return client.generate_content(messages, model=model)


def main():
    """Main function to run the website summary tool."""
    # Get available providers
    providers = LLMFactory.get_providers()
    
    # Choose provider
    print("Available LLM providers:")
    for i, (key, name) in enumerate(providers.items(), 1):
        print(f"{i}. {name}")
    
    choice = input(f"Select provider (1-{len(providers)}, default: 1): ").strip()
    
    try:
        idx = int(choice) - 1 if choice else 0
        if idx < 0 or idx >= len(providers):
            raise ValueError()
        provider_key = list(providers.keys())[idx]
    except (ValueError, IndexError):
        print(f"Invalid choice. Using {list(providers.values())[0]}.")
        provider_key = list(providers.keys())[0]
    
    # Create LLM client
    try:
        client = LLMFactory.create_client(provider_key)
    except Exception as e:
        print(f"Error creating {providers[provider_key]} client: {str(e)}")
        return
    
    # Validate credentials
    is_valid, message = client.validate_credentials()
    if not print_validation_result(is_valid, message):
        return
    
    # Test API connection
    print(f"Testing connection to {providers[provider_key]}...")
    test_response = client.test_connection()
    print("Test API response:")
    print(test_response)
    
    # Choose model
    available_models = client.get_available_models()
    if len(available_models) > 1:
        print("\nAvailable models:")
        for i, model_name in enumerate(available_models, 1):
            print(f"{i}. {model_name}")
        
        model_choice = input(f"Select model (1-{len(available_models)}, default: 1): ").strip()
        try:
            model_idx = int(model_choice) - 1 if model_choice else 0
            if model_idx < 0 or model_idx >= len(available_models):
                raise ValueError()
            model = available_models[model_idx]
        except (ValueError, IndexError):
            print(f"Invalid choice. Using {available_models[0]}.")
            model = available_models[0]
    else:
        model = available_models[0] if available_models else None
    
    # Define website URL to summarize
    website_url = input("Enter the URL of the website to summarize: ")
    
    # Prompt customization option
    customize_prompts = input("Do you want to customize the prompts? (y/n, default: n): ").lower()
    prompt_manager = None
    
    if customize_prompts == 'y':
        print("Current system prompt: ")
        print(PromptManager().system_prompt)
        new_system_prompt = input("Enter new system prompt (leave empty to keep default): ").strip()
        
        print("\nCurrent user prompt template: ")
        print(PromptManager().user_prompt_template)
        new_user_prompt = input("Enter new user prompt template (leave empty to keep default): ").strip()
        
        # Create custom prompt manager if needed
        if new_system_prompt or new_user_prompt:
            system_prompt = new_system_prompt if new_system_prompt else None
            user_prompt = new_user_prompt if new_user_prompt else None
            prompt_manager = PromptManager(system_prompt, user_prompt)
    
    # Ask if user wants to override automatic detection
    override = input("Do you want to override automatic detection of JavaScript-heavy websites? (y/n, default: n): ").lower()
    
    use_selenium = None  # Default to automatic detection
    if override == 'y':
        use_selenium_input = input("Use Selenium for this website? (y/n): ").lower()
        use_selenium = use_selenium_input == 'y'
    
    # Generate and display summary
    print(f"Fetching and summarizing content from {website_url}...")
    summary = summarize_url(client, website_url, use_selenium, model, prompt_manager)
    
    print("\nSummary:")
    print(summary)
    
    # In Jupyter notebook
    try:
        display_summary_markdown(summary)
    except:
        pass  # Not in Jupyter


if __name__ == "__main__":
    main()