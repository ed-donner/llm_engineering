#!/usr/bin/env python
"""Manual test script for email sending via Mailgun."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

from agents.email_providers import MailgunProvider, get_email_provider
from models.cats import Cat, CatMatch, AdoptionAlert, CatProfile

print("="*60)
print("  Tuxedo Link - Email Sending Test")
print("="*60)
print()

# Check if Mailgun key is set
if not os.getenv('MAILGUN_API_KEY'):
    print("❌ MAILGUN_API_KEY not set in environment")
    print("Please set it in your .env file")
    sys.exit(1)

print("✓ Mailgun API key found")
print()

# Create test data
test_cat = Cat(
    id="test-cat-123",
    name="Whiskers",
    age="Young",
    gender="male",
    size="medium",
    breed="Domestic Short Hair",
    description="A playful and friendly cat looking for a loving home!",
    primary_photo="https://via.placeholder.com/400x300?text=Whiskers",
    additional_photos=[],
    city="New York",
    state="NY",
    country="US",
    organization_name="Test Shelter",
    url="https://example.com/cat/123",
    good_with_children=True,
    good_with_dogs=False,
    good_with_cats=True,
    declawed=False,
    house_trained=True,
    spayed_neutered=True,
    special_needs=False,
    shots_current=True,
    adoption_fee=150.0,
    source="test"
)

test_match = CatMatch(
    cat=test_cat,
    match_score=0.95,
    explanation="Great match! Friendly and playful, perfect for families.",
    vector_similarity=0.92,
    attribute_match_score=0.98,
    matching_attributes=["good_with_children", "playful", "medium_size"],
    missing_attributes=[]
)

test_profile = CatProfile(
    user_location="New York, NY",
    max_distance=25,
    age_range=["young", "adult"],
    good_with_children=True,
    good_with_dogs=False,
    good_with_cats=True,
    personality_description="Friendly and playful",
    special_requirements=[]
)

test_alert = AdoptionAlert(
    id=999,
    user_email="test@example.com",  # Replace with your actual email for testing
    profile=test_profile,
    frequency="immediately",
    active=True
)

print("Creating email provider...")
try:
    provider = get_email_provider()  # Uses config.yaml
    print(f"✓ Provider initialized: {provider.get_provider_name()}")
except Exception as e:
    print(f"❌ Failed to initialize provider: {e}")
    sys.exit(1)

print()
print("Preparing test email...")
print(f"  To: {test_alert.user_email}")
print(f"  Subject: Test - New Cat Match on Tuxedo Link!")
print()

# Create EmailAgent to use its template building methods
from agents.email_agent import EmailAgent

email_agent = EmailAgent(provider=provider)

# Build email content
subject = "🐱 Test - New Cat Match on Tuxedo Link!"
html_content = email_agent._build_match_html([test_match], test_alert)
text_content = email_agent._build_match_text([test_match])

# Send test email
print("Sending test email...")
input("Press Enter to send, or Ctrl+C to cancel...")

success = provider.send_email(
    to=test_alert.user_email,
    subject=subject,
    html=html_content,
    text=text_content
)

print()
if success:
    print("✅ Email sent successfully!")
    print()
    print("Please check your inbox at:", test_alert.user_email)
    print()
    print("If you don't see it:")
    print("  1. Check your spam folder")
    print("  2. Verify the email address is correct")
    print("  3. Check Mailgun logs: https://app.mailgun.com/")
else:
    print("❌ Failed to send email")
    print()
    print("Troubleshooting:")
    print("  1. Check MAILGUN_API_KEY is correct")
    print("  2. Verify Mailgun domain in config.yaml")
    print("  3. Check Mailgun account status")
    print("  4. View logs above for error details")

print()
print("="*60)

