"""Profile agent for extracting user preferences using LLM."""

import os
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

from models.cats import CatProfile
from utils.geocoding import parse_location_input
from .agent import Agent


class ProfileAgent(Agent):
    """Agent for extracting cat adoption preferences from user conversation."""
    
    name = "Profile Agent"
    color = Agent.GREEN
    
    MODEL = "gpt-4o-mini"
    
    SYSTEM_PROMPT = """You are a helpful assistant helping users find their perfect cat for adoption.

Your job is to extract their preferences through natural conversation and return them in structured format.

Ask about:
- Color and coat patterns (e.g., tuxedo/black&white, tabby, orange, calico, tortoiseshell, gray, etc.)
- Personality traits they're looking for (playful, calm, cuddly, independent, etc.)
- Age preference (kitten, young adult, adult, senior)
- Size preference (small, medium, large)
- Living situation (children, dogs, other cats)
- Special needs acceptance
- Location and max distance willing to travel
- Gender preference (if any)
- Breed preferences (if any)

IMPORTANT: When users mention colors or patterns (like "tuxedo", "black and white", "orange tabby", etc.), 
extract these into the color_preferences field exactly as the user states them. Examples:
- "tuxedo" → ["tuxedo"]
- "black and white" → ["black and white"]
- "orange tabby" → ["orange", "tabby"]
- "calico" → ["calico"]
- "gray" or "grey" → ["gray"]

Extract colors/patterns naturally without trying to map to specific API values.

Be conversational and warm. Ask follow-up questions if preferences are unclear.
When you have enough information, extract it into the CatProfile format."""
    
    def __init__(self):
        """Initialize the profile agent."""
        load_dotenv()
        
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment")
        
        self.client = OpenAI(api_key=self.api_key)
        
        self.log("Profile Agent initialized")
    
    def extract_profile(self, conversation: List[dict]) -> Optional[CatProfile]:
        """
        Extract CatProfile from conversation history.
        
        Args:
            conversation: List of message dicts with 'role' and 'content'
            
        Returns:
            CatProfile object or None if extraction fails
        """
        self.log("Extracting profile from conversation")
        
        # Add system message
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        messages.extend(conversation)
        
        # Add extraction prompt
        messages.append({
            "role": "user",
            "content": "Please extract my preferences into a structured profile now."
        })
        
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.MODEL,
                messages=messages,
                response_format=CatProfile
            )
            
            profile = response.choices[0].message.parsed
            
            # Parse location if provided
            if profile.user_location:
                coords = parse_location_input(profile.user_location)
                if coords:
                    profile.user_latitude, profile.user_longitude = coords
                    self.log(f"Parsed location: {profile.user_location} -> {coords}")
                else:
                    self.log_warning(f"Could not parse location: {profile.user_location}")
            
            self.log("Profile extracted successfully")
            return profile
            
        except Exception as e:
            self.log_error(f"Failed to extract profile: {e}")
            return None
    
    def chat(self, user_message: str, conversation_history: List[dict]) -> str:
        """
        Continue conversation to gather preferences.
        
        Args:
            user_message: Latest user message
            conversation_history: Previous conversation
            
        Returns:
            Assistant's response
        """
        self.log(f"Processing user message: {user_message[:50]}...")
        
        # Build messages
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages
            )
            
            assistant_message = response.choices[0].message.content
            self.log("Generated response")
            
            return assistant_message
            
        except Exception as e:
            self.log_error(f"Chat failed: {e}")
            return "I'm sorry, I'm having trouble right now. Could you try again?"
    
    def create_profile_from_direct_input(
        self,
        location: str,
        distance: int = 100,
        personality_description: str = "",
        age_range: Optional[List[str]] = None,
        size: Optional[List[str]] = None,
        good_with_children: Optional[bool] = None,
        good_with_dogs: Optional[bool] = None,
        good_with_cats: Optional[bool] = None
    ) -> CatProfile:
        """
        Create profile directly from form inputs (bypass conversation).
        
        Args:
            location: User location
            distance: Search radius in miles
            personality_description: Free text personality description
            age_range: Age preferences
            size: Size preferences
            good_with_children: Must be good with children
            good_with_dogs: Must be good with dogs
            good_with_cats: Must be good with cats
            
        Returns:
            CatProfile object
        """
        self.log("Creating profile from direct input")
        
        # Parse location
        user_lat, user_lon = None, None
        coords = parse_location_input(location)
        if coords:
            user_lat, user_lon = coords
        
        profile = CatProfile(
            user_location=location,
            user_latitude=user_lat,
            user_longitude=user_lon,
            max_distance=distance,
            personality_description=personality_description,
            age_range=age_range,
            size=size,
            good_with_children=good_with_children,
            good_with_dogs=good_with_dogs,
            good_with_cats=good_with_cats
        )
        
        self.log("Profile created from direct input")
        return profile

