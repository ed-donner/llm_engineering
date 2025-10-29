"""Gradio UI for Tuxedo Link cat adoption application."""

import os
import gradio as gr
import pandas as pd
from dotenv import load_dotenv
from typing import List, Optional, Tuple
import logging
import re
from datetime import datetime

# Import models - these are lightweight
from models.cats import CatProfile, CatMatch, AdoptionAlert
from utils.config import is_production

# Load environment
load_dotenv()

# Initialize framework based on mode
framework = None
profile_agent = None

if not is_production():
    # LOCAL MODE: Import and initialize heavy components
    from cat_adoption_framework import TuxedoLinkFramework
    from agents.profile_agent import ProfileAgent
    
    framework = TuxedoLinkFramework()
    profile_agent = ProfileAgent()
    print("✓ Running in LOCAL mode - using local components")
else:
    # PRODUCTION MODE: Don't import heavy components - use Modal API
    print("✓ Running in PRODUCTION mode - using Modal API")

# Global state for current search results
current_matches: List[CatMatch] = []
current_profile: Optional[CatProfile] = None

# Configure logging to suppress verbose output
logging.getLogger().setLevel(logging.WARNING)


def extract_profile_from_text(user_input: str, use_cache: bool = False) -> tuple:
    """
    Extract structured profile from user's natural language input.
    
    Args:
        user_input: User's description of desired cat
        use_cache: Whether to use cached data for search
        
    Returns:
        Tuple of (chat_history, results_html, profile_json)
    """
    global current_matches, current_profile
    
    try:
        # Handle empty input - use placeholder text
        if not user_input or user_input.strip() == "":
            user_input = "I'm looking for a friendly, playful kitten in NYC that's good with children"
        
        # Extract profile using LLM
        # Using messages format for Gradio chatbot
        chat_history = [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": "🔍 Analyzing your preferences..."}
        ]
        
        # Extract profile (Modal or local)
        if is_production():
            # PRODUCTION: Call Modal API
            import modal
            
            # Look up deployed function - correct API!
            extract_profile_func = modal.Function.from_name("tuxedo-link-api", "extract_profile")
            
            print("[INFO] Calling Modal API to extract profile...")
            profile_result = extract_profile_func.remote(user_input)
            
            if not profile_result["success"]:
                return chat_history, "<p>❌ Error extracting profile</p>", "{}"
            
            profile = CatProfile(**profile_result["profile"])
        else:
            # LOCAL: Use local agent
            conversation = [{"role": "user", "content": user_input}]
            profile = profile_agent.extract_profile(conversation)
        
        current_profile = profile
        
        # Perform search
        response_msg = f"✅ Got it! Searching for:\n\n" + \
                       f"📍 Location: {profile.user_location or 'Not specified'}\n" + \
                       f"📏 Distance: {profile.max_distance or 100} miles\n" + \
                       f"🎨 Colors: {', '.join(profile.color_preferences) if profile.color_preferences else 'Any'}\n" + \
                       f"🎭 Personality: {profile.personality_description or 'Any'}\n" + \
                       f"🎂 Age: {', '.join(profile.age_range) if profile.age_range else 'Any'}\n" + \
                       f"👶 Good with children: {'Yes' if profile.good_with_children else 'Not required'}\n" + \
                       f"🐕 Good with dogs: {'Yes' if profile.good_with_dogs else 'Not required'}\n" + \
                       f"🐱 Good with cats: {'Yes' if profile.good_with_cats else 'Not required'}\n\n" + \
                       f"Searching..."
        
        chat_history[1]["content"] = response_msg
        
        # Run search (Modal or local)
        if is_production():
            # PRODUCTION: Call Modal API
            import modal
            
            # Look up deployed function
            search_cats_func = modal.Function.from_name("tuxedo-link-api", "search_cats")
            
            print("[INFO] Calling Modal API to search cats...")
            search_result = search_cats_func.remote(profile.model_dump(), use_cache=use_cache)
            
            if not search_result["success"]:
                error_msg = search_result.get('error', 'Unknown error')
                chat_history.append({"role": "assistant", "content": f"❌ Search error: {error_msg}"})
                return chat_history, "<p>😿 Search failed. Please try again.</p>", profile.json()
            
            # Reconstruct matches from Modal response
            from models.cats import Cat
            current_matches = [
                CatMatch(
                    cat=Cat(**m["cat"]),
                    match_score=m["match_score"],
                    vector_similarity=m["vector_similarity"],
                    attribute_match_score=m["attribute_match_score"],
                    explanation=m["explanation"],
                    matching_attributes=m.get("matching_attributes", []),
                    missing_attributes=m.get("missing_attributes", [])
                )
                for m in search_result["matches"]
            ]
        else:
            # LOCAL: Use local framework
            result = framework.search(profile, use_cache=use_cache)
            current_matches = result.matches
        
        # Build results HTML
        if current_matches:
            chat_history[1]["content"] += f"\n\n✨ Found {len(current_matches)} great matches!"
            results_html = build_results_grid(current_matches)
        else:
            chat_history[1]["content"] += "\n\n😿 No matches found. Try broadening your search criteria."
            results_html = "<p style='text-align:center; color: #666; padding: 40px;'>No matches found</p>"
        
        # Profile JSON for display
        profile_json = profile.model_dump_json(indent=2)
        
        return chat_history, results_html, profile_json
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
        return [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": error_msg}
        ], "<p>Error occurred</p>", "{}"


def build_results_grid(matches: List[CatMatch]) -> str:
    """Build HTML grid of cat results."""
    html = "<div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; padding: 20px;'>"
    
    for match in matches:
        cat = match.cat
        photo = cat.primary_photo or "https://via.placeholder.com/240x180?text=No+Photo"
        
        html += f"""
        <div style='border: 1px solid #ddd; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <img src='{photo}' style='width: 100%; height: 180px; object-fit: cover;' onerror="this.src='https://via.placeholder.com/240x180?text=No+Photo'">
            <div style='padding: 15px;'>
                <h3 style='margin: 0 0 10px 0; color: #333;'>{cat.name}</h3>
                <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                    <span style='background: #4CAF50; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;'>
                        {match.match_score:.0%} Match
                    </span>
                    <span style='color: #666; font-size: 14px;'>{cat.age}</span>
                </div>
                <p style='color: #666; font-size: 14px; margin: 8px 0;'>
                    <strong>{cat.breed}</strong><br/>
                    {cat.city}, {cat.state}<br/>
                    {cat.gender.capitalize()} • {cat.size.capitalize() if cat.size else 'Unknown size'}
                </p>
                <p style='color: #888; font-size: 13px; margin: 10px 0; line-height: 1.4;'>
                    {match.explanation}
                </p>
                <a href='{cat.url}' target='_blank' style='display: block; text-align: center; background: #2196F3; color: white; padding: 10px; border-radius: 5px; text-decoration: none; margin-top: 10px;'>
                    View Details
                </a>
            </div>
        </div>
        """
    
    html += "</div>"
    return html


def search_with_examples(example_text: str, use_cache: bool = False) -> tuple:
    """Handle example button clicks."""
    return extract_profile_from_text(example_text, use_cache)


# ===== ALERT MANAGEMENT FUNCTIONS =====

def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def send_immediate_notification_local(alert_id: int) -> None:
    """
    Send immediate notification locally (not via Modal).
    
    Args:
        alert_id: ID of the alert to process
    """
    from agents.email_agent import EmailAgent
    from agents.email_providers.factory import get_email_provider
    
    print(f"[DEBUG] Sending immediate notification for alert {alert_id}")
    
    # Get alert from database
    alert = framework.db_manager.get_alert_by_id(alert_id)
    if not alert:
        print(f"[ERROR] Alert {alert_id} not found")
        raise ValueError(f"Alert {alert_id} not found")
    
    print(f"[DEBUG] Alert found: email={alert.user_email}, profile exists={alert.profile is not None}")
    
    # Run search with the alert's profile
    result = framework.search(alert.profile, use_cache=False)
    print(f"[DEBUG] Search complete: {len(result.matches)} matches found")
    
    if result.matches:
        # Send email notification
        try:
            email_provider = get_email_provider()
            email_agent = EmailAgent(email_provider)
            print(f"[DEBUG] Sending email to {alert.user_email}...")
            email_agent.send_match_notification(
                alert=alert,
                matches=result.matches
            )
            print(f"[DEBUG] ✓ Email sent successfully!")
        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
            import traceback
            traceback.print_exc()
            raise
    else:
        print(f"[DEBUG] No matches found, no email sent")


def save_alert(email: str, frequency: str, profile_json: str) -> Tuple[str, pd.DataFrame]:
    """
    Save an adoption alert to the database.
    
    Args:
        email: User's email address
        frequency: Notification frequency (Immediately, Daily, Weekly)
        profile_json: JSON string of current search profile
        
    Returns:
        Tuple of (status_message, updated_alerts_dataframe)
    """
    global current_profile
    
    try:
        # Validate email
        if not email or not validate_email(email):
            return "❌ Please enter a valid email address", load_alerts()
        
        # Check if we have a current profile
        if not current_profile:
            return "❌ Please perform a search first to create a profile", load_alerts()
        
        # Normalize frequency
        frequency = frequency.lower()
        
        # Create alert
        alert = AdoptionAlert(
            user_email=email,
            profile=current_profile,
            frequency=frequency,
            active=True
        )
        
        # Save alert based on mode
        if is_production():
            # PRODUCTION MODE: Use Modal function
            try:
                import modal
                
                print(f"[INFO] Production mode: Calling Modal function to create alert...")
                # Look up deployed function - correct API!
                create_alert_func = modal.Function.from_name("tuxedo-link-api", "create_alert_and_notify")
                
                # Send alert data to Modal
                result = create_alert_func.remote(alert.dict())
                
                if result["success"]:
                    status = f"✅ {result['message']}"
                else:
                    status = f"⚠️ {result['message']}"
                
                return status, load_alerts()
                
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                print(f"[ERROR] Modal function failed: {error_detail}")
                return f"❌ Error calling Modal service: {str(e)}\n\nCheck Modal logs for details.", load_alerts()
        else:
            # LOCAL MODE: Save and process locally
            alert_id = framework.db_manager.create_alert(alert)
            
            if frequency == "immediately":
                try:
                    send_immediate_notification_local(alert_id)
                    status = f"✅ Alert saved and notification sent locally! (ID: {alert_id})\n\nCheck your email at {email}"
                except Exception as e:
                    import traceback
                    error_detail = traceback.format_exc()
                    print(f"[ERROR] Local notification failed: {error_detail}")
                    status = f"✅ Alert saved (ID: {alert_id}), but notification failed: {str(e)}"
            else:
                status = f"✅ Alert saved successfully! (ID: {alert_id})\n\nYou'll receive {frequency} notifications at {email}"
            
            return status, load_alerts()
        
    except Exception as e:
        return f"❌ Error saving alert: {str(e)}", load_alerts()


def load_alerts(email_filter: str = "") -> pd.DataFrame:
    """
    Load all alerts from the database.
    
    Args:
        email_filter: Optional email to filter by
        
    Returns:
        DataFrame of alerts
    """
    try:
        # Get alerts from database (Modal or local)
        if is_production():
            # PRODUCTION: Call Modal API
            import modal
            
            # Look up deployed function
            get_alerts_func = modal.Function.from_name("tuxedo-link-api", "get_alerts")
            
            alert_dicts = get_alerts_func.remote(email=email_filter if email_filter and validate_email(email_filter) else None)
            alerts = [AdoptionAlert(**a) for a in alert_dicts]
        else:
            # LOCAL: Use local database
            if email_filter and validate_email(email_filter):
                alerts = framework.db_manager.get_alerts_by_email(email_filter)
            else:
                alerts = framework.db_manager.get_all_alerts()
        
        if not alerts:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=["ID", "Email", "Frequency", "Location", "Preferences", "Last Sent", "Status"])
        
        # Convert to display format
        data = []
        for alert in alerts:
            location = alert.profile.user_location or "Any"
            prefs = []
            if alert.profile.age_range:
                prefs.append(f"Age: {', '.join(alert.profile.age_range)}")
            if alert.profile.good_with_children:
                prefs.append("Child-friendly")
            if alert.profile.good_with_dogs:
                prefs.append("Dog-friendly")
            if alert.profile.good_with_cats:
                prefs.append("Cat-friendly")
            
            prefs_str = ", ".join(prefs) if prefs else "Any"
            
            last_sent = alert.last_sent.strftime("%Y-%m-%d %H:%M") if alert.last_sent else "Never"
            status = "🟢 Active" if alert.active else "🔴 Inactive"
            
            data.append({
                "ID": alert.id,
                "Email": alert.user_email,
                "Frequency": alert.frequency.capitalize(),
                "Location": location,
                "Preferences": prefs_str,
                "Last Sent": last_sent,
                "Status": status
            })
        
        return pd.DataFrame(data)
        
    except Exception as e:
        logging.error(f"Error loading alerts: {e}")
        return pd.DataFrame(columns=["ID", "Email", "Frequency", "Location", "Preferences", "Last Sent", "Status"])


def delete_alert(alert_id: str, email_filter: str = "") -> Tuple[str, pd.DataFrame]:
    """
    Delete an alert by ID.
    
    Args:
        alert_id: Alert ID to delete
        email_filter: Optional email filter for refresh
        
    Returns:
        Tuple of (status_message, updated_alerts_dataframe)
    """
    try:
        if not alert_id:
            return "❌ Please enter an Alert ID", load_alerts(email_filter)
        
        # Convert to int
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            return f"❌ Invalid Alert ID: {alert_id}", load_alerts(email_filter)
        
        # Delete from database (Modal or local)
        if is_production():
            # PRODUCTION: Call Modal API
            import modal
            
            # Look up deployed function
            delete_alert_func = modal.Function.from_name("tuxedo-link-api", "delete_alert")
            success = delete_alert_func.remote(alert_id_int)
            if not success:
                return f"❌ Failed to delete alert {alert_id}", load_alerts(email_filter)
        else:
            # LOCAL: Use local database
            framework.db_manager.delete_alert(alert_id_int)
        
        return f"✅ Alert {alert_id} deleted successfully", load_alerts(email_filter)
        
    except Exception as e:
        return f"❌ Error deleting alert: {str(e)}", load_alerts(email_filter)


def toggle_alert_status(alert_id: str, email_filter: str = "") -> Tuple[str, pd.DataFrame]:
    """
    Toggle alert active/inactive status.
    
    Args:
        alert_id: Alert ID to toggle
        email_filter: Optional email filter for refresh
        
    Returns:
        Tuple of (status_message, updated_alerts_dataframe)
    """
    try:
        if not alert_id:
            return "❌ Please enter an Alert ID", load_alerts(email_filter)
        
        # Convert to int
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            return f"❌ Invalid Alert ID: {alert_id}", load_alerts(email_filter)
        
        # Get current alert and toggle (Modal or local)
        if is_production():
            # PRODUCTION: Call Modal API
            import modal
            
            # Look up deployed functions
            get_alerts_func = modal.Function.from_name("tuxedo-link-api", "get_alerts")
            update_alert_func = modal.Function.from_name("tuxedo-link-api", "update_alert")
            
            # Get all alerts and find this one
            alert_dicts = get_alerts_func.remote()
            alert_dict = next((a for a in alert_dicts if a["id"] == alert_id_int), None)
            
            if not alert_dict:
                return f"❌ Alert {alert_id} not found", load_alerts(email_filter)
            
            alert = AdoptionAlert(**alert_dict)
            new_status = not alert.active
            
            success = update_alert_func.remote(alert_id_int, active=new_status)
            if not success:
                return f"❌ Failed to update alert {alert_id}", load_alerts(email_filter)
        else:
            # LOCAL: Use local database
            alert = framework.db_manager.get_alert(alert_id_int)
            if not alert:
                return f"❌ Alert {alert_id} not found", load_alerts(email_filter)
            
            new_status = not alert.active
            framework.db_manager.update_alert(alert_id_int, active=new_status)
        
        status_text = "activated" if new_status else "deactivated"
        return f"✅ Alert {alert_id} {status_text}", load_alerts(email_filter)
        
    except Exception as e:
        return f"❌ Error toggling alert: {str(e)}", load_alerts(email_filter)


def build_search_tab() -> None:
    """Build the search tab interface with chat and results display."""
    with gr.Column():
        gr.Markdown("# 🐱 Find Your Perfect Cat")
        gr.Markdown("Tell me what kind of cat you're looking for, and I'll help you find the perfect match!")
        
        with gr.Row():
            # In production mode, default to False since Modal cache starts empty
            # In local mode, can default to True after first run
            default_cache = False if is_production() else True
            use_cache_checkbox = gr.Checkbox(
                label="Use Cache (Fast Mode)",
                value=default_cache,
                info="Use cached cat data for faster searches (uncheck for fresh data from APIs)"
            )
        
        # Chat interface for natural language input
        chatbot = gr.Chatbot(label="Chat", height=200, type="messages")
        user_input = gr.Textbox(
            label="Describe your ideal cat",
            placeholder="I'm looking for a friendly, playful kitten in NYC that's good with children...",
            lines=3
        )
        
        with gr.Row():
            submit_btn = gr.Button("🔍 Search", variant="primary")
            clear_btn = gr.Button("🔄 Clear")
        
        # Example queries
        gr.Markdown("### 💡 Try these examples:")
        with gr.Row():
            example_btns = [
                gr.Button("🏠 Family cat", size="sm"),
                gr.Button("🎮 Playful kitten", size="sm"),
                gr.Button("😴 Calm adult", size="sm"),
                gr.Button("👶 Good with kids", size="sm")
            ]
        
        # Results display
        gr.Markdown("---")
        gr.Markdown("## 🎯 Search Results")
        results_html = gr.HTML(value="<p style='text-align:center; color: #999; padding: 40px;'>Enter your preferences above to start searching</p>")
        
        # Profile display (collapsible)
        with gr.Accordion("📋 Extracted Profile (for debugging)", open=False):
            profile_display = gr.JSON(label="Profile Data")
        
        # Wire up events
        submit_btn.click(
            fn=extract_profile_from_text,
            inputs=[user_input, use_cache_checkbox],
            outputs=[chatbot, results_html, profile_display]
        )
        
        user_input.submit(
            fn=extract_profile_from_text,
            inputs=[user_input, use_cache_checkbox],
            outputs=[chatbot, results_html, profile_display]
        )
        
        clear_btn.click(
            fn=lambda: ([], "<p style='text-align:center; color: #999; padding: 40px;'>Enter your preferences above to start searching</p>", ""),
            outputs=[chatbot, results_html, profile_display]
        )
        
        # Example buttons
        examples = [
            "I want a friendly family cat in zip code 10001, good with children and dogs",
            "Looking for a playful young kitten near New York City",
            "I need a calm, affectionate adult cat that likes to cuddle",
            "Show me cats good with children in the NYC area"
        ]
        
        for btn, example in zip(example_btns, examples):
            btn.click(
                fn=search_with_examples,
                inputs=[gr.State(example), use_cache_checkbox],
                outputs=[chatbot, results_html, profile_display]
            )


def build_alerts_tab() -> None:
    """Build the alerts management tab for scheduling email notifications."""
    with gr.Column():
        gr.Markdown("# 🔔 Manage Alerts")
        gr.Markdown("Save your search and get notified when new matching cats are available!")
        
        # Instructions
        gr.Markdown("""
        ### How it works:
        1. **Search** for cats using your preferred criteria in the Search tab
        2. **Enter your email** below and choose notification frequency
        3. **Save Alert** to start receiving notifications
        
        You'll be notified when new cats matching your preferences become available!
        """)
        
        # Save Alert Section
        gr.Markdown("### 💾 Save Current Search as Alert")
        
        with gr.Row():
            with gr.Column(scale=2):
                email_input = gr.Textbox(
                    label="Email Address",
                    placeholder="your@email.com",
                    info="Where should we send notifications?"
                )
            with gr.Column(scale=1):
                frequency_dropdown = gr.Dropdown(
                    label="Notification Frequency",
                    choices=["Immediately", "Daily", "Weekly"],
                    value="Daily",
                    info="How often to check for new matches"
                )
        
        with gr.Row():
            save_btn = gr.Button("💾 Save Alert", variant="primary", scale=2)
            profile_display = gr.JSON(
                label="Current Search Profile",
                value={},
                visible=False,
                scale=1
            )
        
        save_status = gr.Markdown("")
        
        gr.Markdown("---")
        
        # Manage Alerts Section
        gr.Markdown("### 📋 Your Saved Alerts")
        
        with gr.Row():
            with gr.Column(scale=2):
                email_filter_input = gr.Textbox(
                    label="Filter by Email (optional)",
                    placeholder="your@email.com"
                )
            with gr.Column(scale=1):
                refresh_btn = gr.Button("🔄 Refresh", size="sm")
        
        alerts_table = gr.Dataframe(
            value=[],  # Start empty - load on demand to avoid blocking UI startup
            headers=["ID", "Email", "Frequency", "Location", "Preferences", "Last Sent", "Status"],
            datatype=["number", "str", "str", "str", "str", "str", "str"],
            interactive=False,
            wrap=True
        )
        
        # Alert Actions
        gr.Markdown("### ⚙️ Manage Alert")
        with gr.Row():
            alert_id_input = gr.Textbox(
                label="Alert ID",
                placeholder="Enter Alert ID from table above",
                scale=2
            )
            with gr.Column(scale=3):
                with gr.Row():
                    toggle_btn = gr.Button("🔄 Toggle Active/Inactive", size="sm")
                    delete_btn = gr.Button("🗑️ Delete Alert", variant="stop", size="sm")
        
        action_status = gr.Markdown("")
        
        # Wire up events
        save_btn.click(
            fn=save_alert,
            inputs=[email_input, frequency_dropdown, profile_display],
            outputs=[save_status, alerts_table]
        )
        
        refresh_btn.click(
            fn=load_alerts,
            inputs=[email_filter_input],
            outputs=[alerts_table]
        )
        
        email_filter_input.submit(
            fn=load_alerts,
            inputs=[email_filter_input],
            outputs=[alerts_table]
        )
        
        toggle_btn.click(
            fn=toggle_alert_status,
            inputs=[alert_id_input, email_filter_input],
            outputs=[action_status, alerts_table]
        )
        
        delete_btn.click(
            fn=delete_alert,
            inputs=[alert_id_input, email_filter_input],
            outputs=[action_status, alerts_table]
        )


def build_about_tab() -> None:
    """Build the about tab with Kyra's story and application info."""
    with gr.Column():
        gr.Markdown("# 🎩 About Tuxedo Link")
        
        gr.Markdown("""
        ## In Loving Memory of Kyra 🐱
        
        This application is dedicated to **Kyra**, a beloved companion who brought joy, 
        comfort, and unconditional love to our lives. Kyra was more than just a cat—
        he was family, a friend, and a constant source of happiness.
        
        ### The Inspiration
        
        Kyra Link was created to help others find their perfect feline companion, 
        just as Kyra found his way into our hearts. Every cat deserves a loving home, 
        and every person deserves the companionship of a wonderful cat like Kyra.
        
        ### The Technology
        
        This application uses AI and machine learning to match prospective 
        adopters with their ideal cat:
        
        - **Natural Language Processing**: Understand your preferences in plain English
        - **Semantic Search**: Find cats based on personality, not just keywords
        - **Multi-Source Aggregation**: Search across multiple adoption platforms
        - **Smart Deduplication**: Remove duplicate listings using AI
        - **Image Recognition**: Match cats visually using computer vision
        - **Hybrid Matching**: Combine semantic understanding with structured filters
        
        ### Features
        
        ✅ **Multi-Platform Search**: Petfinder, RescueGroups  
        ✅ **AI-Powered Matching**: Semantic search with vector embeddings  
        ✅ **Smart Deduplication**: Name, description, and image similarity   
        ✅ **Personality Matching**: Find cats that match your lifestyle  
        ✅ **Location-Based**: Search near you with customizable radius  
        
        ### Technical Stack
        
        - **Frontend**: Gradio
        - **Backend**: Python with Modal serverless
        - **LLMs**: OpenAI GPT-4 for profile extraction
        - **Vector DB**: ChromaDB with SentenceTransformers
        - **Image AI**: CLIP for visual similarity
        - **APIs**: Petfinder, RescueGroups, SendGrid
        - **Database**: SQLite for caching and user management
        
        ### Open Source
        
        Tuxedo Link is open source and built as part of the Andela LLM Engineering bootcamp.
        Contributions and improvements are welcome!
        
        ### Acknowledgments
        
        - **Petfinder**: For their comprehensive pet adoption API
        - **RescueGroups**: For connecting rescues with adopters
        - **Andela**: For the LLM Engineering bootcamp
        - **Kyra**: For inspiring this project and bringing so much joy 💙
        
        ---
        
        *"In memory of Kyra, who taught us that home is wherever your cat is."*
        
        🐾 **May every cat find their perfect home** 🐾
        """)
        
        # Add Kyra's picture
        with gr.Row():
            with gr.Column():
                gr.Image(
                    value="assets/Kyra.png",
                    label="Kyra - Forever in our hearts 💙",
                    show_label=True,
                    container=True,
                    width=400,
                    height=400,
                    show_download_button=False,
                    show_share_button=False,
                    interactive=False
                )


def create_app() -> gr.Blocks:
    """
    Create and configure the Gradio application.
    
    Returns:
        Configured Gradio Blocks application
    """
    with gr.Blocks(
        title="Tuxedo Link - Find Your Perfect Cat",
        theme=gr.themes.Soft()
    ) as app:
        gr.Markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='font-size: 3em; margin: 0;'>🎩 Tuxedo Link</h1>
            <p style='font-size: 1.2em; color: #666; margin: 10px 0;'>
                AI-Powered Cat Adoption Search
            </p>
        </div>
        """)
        
        with gr.Tabs():
            with gr.Tab("🔍 Search"):
                build_search_tab()
            
            with gr.Tab("🔔 Alerts"):
                build_alerts_tab()
            
            with gr.Tab("ℹ️ About"):
                build_about_tab()
        
        gr.Markdown("""
        <div style='text-align: center; padding: 20px; color: #999; font-size: 0.9em;'>
            Made with ❤️ in memory of Kyra | 
            <a href='https://github.com/yourusername/tuxedo-link' style='color: #2196F3;'>GitHub</a> | 
            Powered by AI & Open Source
        </div>
        """)
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

