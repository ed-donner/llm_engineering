"""Email agent for sending match notifications."""

from typing import List, Optional
from datetime import datetime

from agents.agent import Agent
from agents.email_providers import get_email_provider, EmailProvider
from models.cats import CatMatch, AdoptionAlert
from utils.timing import timed
from utils.config import get_email_config


class EmailAgent(Agent):
    """Agent for sending email notifications about cat matches."""
    
    name = "Email Agent"
    color = '\033[35m'  # Magenta
    
    def __init__(self, provider: Optional[EmailProvider] = None):
        """
        Initialize the email agent.
        
        Args:
            provider: Optional email provider instance. If None, creates from config.
        """
        super().__init__()
        
        try:
            self.provider = provider or get_email_provider()
            self.enabled = True
            self.log(f"Email Agent initialized with provider: {self.provider.get_provider_name()}")
        except Exception as e:
            self.log_error(f"Failed to initialize email provider: {e}")
            self.log_warning("Email notifications disabled")
            self.enabled = False
            self.provider = None
    
    def _build_match_html(self, matches: List[CatMatch], alert: AdoptionAlert) -> str:
        """
        Build HTML email content for matches.
        
        Args:
            matches: List of cat matches
            alert: Adoption alert with user preferences
            
        Returns:
            HTML email content
        """
        # Header
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5em;
                }}
                .cat-card {{
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    overflow: hidden;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .cat-photo {{
                    width: 100%;
                    height: 300px;
                    object-fit: cover;
                }}
                .cat-details {{
                    padding: 20px;
                }}
                .cat-name {{
                    font-size: 1.8em;
                    color: #333;
                    margin: 0 0 10px 0;
                }}
                .match-score {{
                    background: #4CAF50;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    display: inline-block;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .cat-info {{
                    color: #666;
                    margin: 10px 0;
                }}
                .cat-description {{
                    color: #888;
                    line-height: 1.8;
                    margin: 15px 0;
                }}
                .view-button {{
                    display: inline-block;
                    background: #2196F3;
                    color: white;
                    padding: 12px 30px;
                    border-radius: 5px;
                    text-decoration: none;
                    font-weight: bold;
                    margin-top: 10px;
                }}
                .footer {{
                    text-align: center;
                    color: #999;
                    padding: 30px 0;
                    border-top: 1px solid #eee;
                    margin-top: 30px;
                }}
                .unsubscribe {{
                    color: #999;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎩 Tuxedo Link</h1>
                <p>We found {len(matches)} new cat{'s' if len(matches) != 1 else ''} matching your preferences!</p>
            </div>
        """
        
        # Cat cards
        for match in matches[:10]:  # Limit to top 10 for email
            cat = match.cat
            photo = cat.primary_photo or "https://via.placeholder.com/800x300?text=No+Photo"
            
            html += f"""
            <div class="cat-card">
                <img src="{photo}" alt="{cat.name}" class="cat-photo">
                <div class="cat-details">
                    <h2 class="cat-name">{cat.name}</h2>
                    <div class="match-score">{match.match_score:.0%} Match</div>
                    <div class="cat-info">
                        <strong>{cat.breed}</strong><br/>
                        📍 {cat.city}, {cat.state}<br/>
                        🎂 {cat.age} • {cat.gender.capitalize()} • {cat.size.capitalize() if cat.size else 'Size not specified'}<br/>
            """
            
            # Add special attributes
            attrs = []
            if cat.good_with_children:
                attrs.append("👶 Good with children")
            if cat.good_with_dogs:
                attrs.append("🐕 Good with dogs")
            if cat.good_with_cats:
                attrs.append("🐱 Good with cats")
            
            if attrs:
                html += "<br/>" + " • ".join(attrs)
            
            html += f"""
                    </div>
                    <div class="cat-description">
                        <strong>Why this is a great match:</strong><br/>
                        {match.explanation}
                    </div>
            """
            
            # Add description if available
            if cat.description:
                desc = cat.description[:300] + "..." if len(cat.description) > 300 else cat.description
                html += f"""
                    <div class="cat-description">
                        <strong>About {cat.name}:</strong><br/>
                        {desc}
                    </div>
                """
            
            html += f"""
                    <a href="{cat.url}" class="view-button">View {cat.name}'s Profile →</a>
                </div>
            </div>
            """
        
        # Footer
        html += f"""
            <div class="footer">
                <p>This email was sent because you saved a search on Tuxedo Link.</p>
                <p>
                    <a href="http://localhost:7860" class="unsubscribe">Manage Alerts</a> | 
                    <a href="http://localhost:7860" class="unsubscribe">Unsubscribe</a>
                </p>
                <p>Made with ❤️ in memory of Tuxedo</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _build_match_text(self, matches: List[CatMatch]) -> str:
        """
        Build plain text email content for matches.
        
        Args:
            matches: List of cat matches
            
        Returns:
            Plain text email content
        """
        text = f"TUXEDO LINK - New Matches Found!\n\n"
        text += f"We found {len(matches)} cat{'s' if len(matches) != 1 else ''} matching your preferences!\n\n"
        text += "="*60 + "\n\n"
        
        for i, match in enumerate(matches[:10], 1):
            cat = match.cat
            text += f"{i}. {cat.name} - {match.match_score:.0%} Match\n"
            text += f"   {cat.breed}\n"
            text += f"   {cat.city}, {cat.state}\n"
            text += f"   {cat.age} • {cat.gender} • {cat.size or 'Size not specified'}\n"
            text += f"   Match: {match.explanation}\n"
            text += f"   View: {cat.url}\n\n"
        
        text += "="*60 + "\n"
        text += "Manage your alerts: http://localhost:7860\n"
        text += "Made with love in memory of Tuxedo\n"
        
        return text
    
    @timed
    def send_match_notification(
        self,
        alert: AdoptionAlert,
        matches: List[CatMatch]
    ) -> bool:
        """
        Send email notification about new matches.
        
        Args:
            alert: Adoption alert with user email and preferences
            matches: List of cat matches to notify about
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            self.log_warning("Email agent disabled - skipping notification")
            return False
        
        if not matches:
            self.log("No matches to send")
            return False
        
        try:
            # Build email content
            subject = f"🐱 {len(matches)} New Cat Match{'es' if len(matches) != 1 else ''} on Tuxedo Link!"
            html_content = self._build_match_html(matches, alert)
            text_content = self._build_match_text(matches)
            
            # Send via provider
            self.log(f"Sending notification to {alert.user_email} for {len(matches)} matches")
            success = self.provider.send_email(
                to=alert.user_email,
                subject=subject,
                html=html_content,
                text=text_content
            )
            
            if success:
                self.log(f"✅ Email sent successfully")
                return True
            else:
                self.log_error(f"Failed to send email")
                return False
                
        except Exception as e:
            self.log_error(f"Error sending email: {e}")
            return False
    
    @timed
    def send_welcome_email(self, user_email: str, user_name: str = None) -> bool:
        """
        Send welcome email when user creates an alert.
        
        Args:
            user_email: User's email address
            user_name: User's name (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            greeting = f"Hi {user_name}" if user_name else "Hello"
            
            subject = "Welcome to Tuxedo Link! 🐱"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 40px;
                        border-radius: 10px;
                        text-align: center;
                    }}
                    .content {{
                        padding: 30px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎩 Welcome to Tuxedo Link!</h1>
                </div>
                <div class="content">
                    <p>{greeting}!</p>
                    <p>Thank you for signing up for cat adoption alerts. We're excited to help you find your perfect feline companion!</p>
                    <p>We'll notify you when new cats matching your preferences become available for adoption.</p>
                    <p><strong>What happens next?</strong></p>
                    <ul>
                        <li>We'll search across multiple adoption platforms</li>
                        <li>You'll receive email notifications based on your preferences</li>
                        <li>You can manage your alerts anytime at <a href="http://localhost:7860">Tuxedo Link</a></li>
                    </ul>
                    <p>Happy cat hunting! 🐾</p>
                    <p style="color: #999; font-style: italic;">In loving memory of Kyra</p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            {greeting}!
            
            Thank you for signing up for Tuxedo Link cat adoption alerts!
            
            We'll notify you when new cats matching your preferences become available.
            
            What happens next?
            - We'll search across multiple adoption platforms
            - You'll receive email notifications based on your preferences
            - Manage your alerts at: http://localhost:7860
            
            Happy cat hunting!
            
            In loving memory of Kyra
            """
            
            success = self.provider.send_email(
                to=user_email,
                subject=subject,
                html=html_content,
                text=text_content
            )
            
            return success
            
        except Exception as e:
            self.log_error(f"Error sending welcome email: {e}")
            return False

