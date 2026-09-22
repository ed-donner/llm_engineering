"""
Prompt templates for the Website Brochure Generator.

This module contains all the system and user prompts used for:
- Link analysis and filtering
- Brochure generation
"""


def get_links_system_prompt() -> str:
    """Get the system prompt for link analysis."""
    return """You are provided with a list of links found on a webpage. 
You are able to decide which of the links would be most relevant to include in a brochure about the company. 
Relevant links usually include: About page, Company page, Careers/Jobs pages, News page, Products/Services page.

Always respond in JSON exactly like this:
{
    "links": [
        {"type": "<page type>", "url": "<full URL>"},
        {"type": "<page type>", "url": "<full URL>"}
    ]
}

If no relevant links are found, return:
{
    "links": []
}

If multiple links could map to the same type (e.g. two About pages), include the best candidate only.

You should respond in JSON as in the below examples:

## Example 1
Input links:
- https://acme.com/about  
- https://acme.com/pricing  
- https://acme.com/blog  
- https://acme.com/signup  

Output:
{
"links": [
    {"type": "about page", "url": "https://acme.com/about"},
    {"type": "blog page", "url": "https://acme.com/blog"},
    {"type": "pricing page", "url": "https://acme.com/pricing"}
]
}

## Example 2
Input links:
- https://startup.io/  
- https://startup.io/company  
- https://startup.io/careers  
- https://startup.io/support  

Output:
{
"links": [
    {"type": "company page", "url": "https://startup.io/company"},
    {"type": "careers page", "url": "https://startup.io/careers"}
]
}

## Example 3
Input links:
- https://coolapp.xyz/login  
- https://coolapp.xyz/random  

Output:
{
"links": []
}"""


def get_links_user_prompt(website_data: dict) -> str:
    """Get the user prompt for link analysis."""
    prompt = f"Here is the list of links on the website of {website_data['url']} - "
    prompt += "please decide which of these are relevant web links for a brochure about the company, respond with the full https URL in JSON format.\n"
    prompt += "Do not include Terms of Service, Privacy, email links, or login pages.\n"
    prompt += "Links (some might be relative links):\n"
    
    for link in website_data["links"]:
        prompt += f"- {link['url']} (text: {link['text']})\n"
    
    return prompt


def get_brochure_system_prompt() -> str:
    """Get the system prompt for brochure generation."""
    return """You are an assistant that analyzes the contents of several relevant pages from a company website 
and creates a short brochure about the company for prospective customers, investors and recruits. 

Respond in markdown format with the following structure:
# Company Name

## About
[Brief company description]

## Products/Services
[What the company offers]

## Company Culture
[Work environment, values, team]

## Careers
[Job opportunities, benefits, growth]

## Contact
[How to reach the company]

Keep the brochure concise but informative, focusing on the most important aspects that would interest potential customers, investors, and job seekers."""


def get_brochure_user_prompt(website_data: dict, additional_pages: list) -> str:
    """Get the user prompt for brochure generation."""
    prompt = f"You are looking at company details for: {website_data['url']}\n"
    prompt += f"Company: {website_data['title']}\n\n"
    prompt += "Here are the contents of its landing page and other relevant pages; use this information to build a short brochure of the company in markdown.\n\n"
    
    # Add main page content
    prompt += f"## Landing Page Content:\n{website_data['content'][:5000]}\n\n"
    
    # Add additional pages content
    for page in additional_pages:
        if page.get("status") == "success":
            prompt += f"## {page.get('type', 'Additional Page')} Content:\n{page['content'][:3000]}\n\n"
    
    # Truncate if too long
    if len(prompt) > 15000:
        prompt = prompt[:15000] + "\n\n[Content truncated for length]"
    
    return prompt


# Optional: You could also create prompt templates for different brochure styles
def get_brochure_system_prompt_technical() -> str:
    """Alternative system prompt for more technical brochures."""
    return """You are an assistant that creates technical brochures for companies. 
Focus on technical capabilities, infrastructure, and engineering excellence.
Include sections for: Technical Stack, Engineering Team, Innovation, and Technical Partnerships."""


def get_brochure_system_prompt_startup() -> str:
    """Alternative system prompt for startup-focused brochures."""
    return """You are an assistant that creates startup-focused brochures. 
Emphasize growth potential, market opportunity, and team vision.
Include sections for: Mission & Vision, Market Opportunity, Growth Metrics, and Team."""


# Prompt configuration
PROMPT_VARIANTS = {
    "default": get_brochure_system_prompt,
    "technical": get_brochure_system_prompt_technical,
    "startup": get_brochure_system_prompt_startup,
}
