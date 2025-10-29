"""Modal scheduled search service for running automated cat searches."""

import modal
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

# Local imports - available because we use .add_local_dir() to copy all project files
from cat_adoption_framework import TuxedoLinkFramework
from database.manager import DatabaseManager
from agents.email_agent import EmailAgent
from agents.email_providers.factory import get_email_provider

# Create Modal app
app = modal.App("tuxedo-link-scheduled-search")

# Get project directory
project_dir = Path(__file__).parent

# Define image with all dependencies and project files
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "openai",
        "chromadb",
        "sentence-transformers==2.5.1",  # Compatible with torch 2.2.2
        "transformers==4.38.0",  # Compatible with torch 2.2.2
        "python-dotenv",
        "pydantic",
        "requests",
        "sendgrid",
        "pyyaml",
        "python-levenshtein",
        "Pillow",
        "geopy",
        "open-clip-torch==2.24.0",  # Compatible with torch 2.2.2
    )
    .apt_install("git")
    .run_commands(
        "pip install torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu",
        "pip install numpy==1.26.4",
    )
    # Add only necessary source directories (Modal 1.0+ API)
    .add_local_dir(str(project_dir / "models"), remote_path="/root/models")
    .add_local_dir(str(project_dir / "agents"), remote_path="/root/agents")
    .add_local_dir(str(project_dir / "database"), remote_path="/root/database")
    .add_local_dir(str(project_dir / "utils"), remote_path="/root/utils")
    # Add standalone Python files
    .add_local_file(str(project_dir / "cat_adoption_framework.py"), remote_path="/root/cat_adoption_framework.py")
    .add_local_file(str(project_dir / "setup_vectordb.py"), remote_path="/root/setup_vectordb.py")
    .add_local_file(str(project_dir / "setup_metadata_vectordb.py"), remote_path="/root/setup_metadata_vectordb.py")
    # Add config file
    .add_local_file(str(project_dir / "config.yaml"), remote_path="/root/config.yaml")
)

# Create Volume for persistent storage (database and vector store)
volume = modal.Volume.from_name("tuxedo-link-data", create_if_missing=True)

# Define secrets
secrets = [
    modal.Secret.from_name("tuxedo-link-secrets")  # Contains all API keys
]


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=600,  # 10 minutes
)
def run_scheduled_searches() -> None:
    """
    Run scheduled searches for all active alerts.
    
    This function:
    1. Loads all active adoption alerts from database
    2. For each alert, runs a cat search based on saved profile
    3. If new matches found, sends email notification
    4. Updates alert last_sent timestamp
    """
    print(f"[{datetime.now()}] Starting scheduled search job")
    
    # Initialize components
    framework = TuxedoLinkFramework()
    db_manager = DatabaseManager("/data/tuxedo_link.db")
    email_agent = EmailAgent()
    
    # Get all active alerts
    alerts = db_manager.get_active_alerts()
    print(f"Found {len(alerts)} active alerts")
    
    for alert in alerts:
        try:
            print(f"Processing alert {alert.id} for {alert.user_email}")
            
            # Run search
            result = framework.search(alert.profile)
            
            # Filter out cats already seen
            new_matches = [
                m for m in result.matches
                if m.cat.id not in alert.last_match_ids
            ]
            
            if new_matches:
                print(f"Found {len(new_matches)} new matches for alert {alert.id}")
                
                # Send email
                if email_agent.enabled:
                    email_sent = email_agent.send_match_notification(alert, new_matches)
                    if email_sent:
                        # Update last_sent and last_match_ids
                        new_match_ids = [m.cat.id for m in new_matches]
                        db_manager.update_alert(
                            alert.id,
                            last_sent=datetime.now(),
                            last_match_ids=new_match_ids
                        )
                        print(f"Email sent successfully for alert {alert.id}")
                    else:
                        print(f"Failed to send email for alert {alert.id}")
                else:
                    print("Email agent disabled")
            else:
                print(f"No new matches for alert {alert.id}")
                
        except Exception as e:
            print(f"Error processing alert {alert.id}: {e}")
            continue
    
    print(f"[{datetime.now()}] Scheduled search job completed")


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=300,
)
def send_immediate_notification(alert_id: int) -> bool:
    """
    Send immediate notification for a specific alert.
    
    This is called when an alert is created with frequency="immediately".
    
    Args:
        alert_id: The ID of the alert to process
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    import sys
    import os
    
    # Add project root to path
    print(f"[{datetime.now()}] Processing immediate notification for alert {alert_id}")
    
    try:
        # Initialize components
        framework = TuxedoLinkFramework()
        db_manager = DatabaseManager("/data/tuxedo_link.db")
        email_agent = EmailAgent()
        
        # Get the alert
        alert = db_manager.get_alert(alert_id)
        if not alert:
            print(f"Alert {alert_id} not found")
            return False
        
        if not alert.active:
            print(f"Alert {alert_id} is inactive")
            return False
        
        # Run search
        result = framework.search(alert.profile)
        
        if result.matches:
            print(f"Found {len(result.matches)} matches for alert {alert_id}")
            
            # Send email
            if email_agent.enabled:
                email_sent = email_agent.send_match_notification(alert, result.matches)
                if email_sent:
                    # Update last_sent and last_match_ids
                    match_ids = [m.cat.id for m in result.matches]
                    db_manager.update_alert(
                        alert.id,
                        last_sent=datetime.now(),
                        last_match_ids=match_ids
                    )
                    print(f"Email sent successfully for alert {alert_id}")
                    return True
                else:
                    print(f"Failed to send email for alert {alert_id}")
                    return False
            else:
                print("Email agent disabled")
                return False
        else:
            print(f"No matches found for alert {alert_id}")
            return False
            
    except Exception as e:
        print(f"Error processing immediate notification for alert {alert_id}: {e}")
        return False


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=300,
)
def create_alert_and_notify(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an alert in Modal's database and send immediate notification.
    
    This is called from the UI in production mode when creating an alert.
    The alert is saved to Modal's database, then processed if immediate.
    
    Args:
        alert_data: Dictionary containing alert data (from AdoptionAlert.dict())
        
    Returns:
        Dict with {"success": bool, "alert_id": int, "message": str}
    """
    import sys
    import os
    
    # Add project root to path
    print(f"[{datetime.now()}] Creating alert in Modal DB")
    
    try:
        # Initialize database
        db_manager = DatabaseManager("/data/tuxedo_link.db")
        
        # Reconstruct alert from dict
        alert = AdoptionAlert(**alert_data)
        print(f"Alert for: {alert.user_email}, location: {alert.profile.user_location if alert.profile else 'None'}")
        
        # Save alert to Modal's database
        alert_id = db_manager.create_alert(alert)
        print(f"✓ Alert created in Modal DB with ID: {alert_id}")
        
        # Update alert with the ID
        alert.id = alert_id
        
        # If immediate frequency, send notification now
        if alert.frequency == "immediately":
            print(f"Sending immediate notification...")
            framework = TuxedoLinkFramework()
            email_provider = get_email_provider()
            email_agent = EmailAgent(email_provider)
            
            # Run search
            result = framework.search(alert.profile, use_cache=False)
            
            if result.matches:
                print(f"Found {len(result.matches)} matches")
                
                # Send email
                if email_agent.enabled:
                    email_sent = email_agent.send_match_notification(alert, result.matches)
                    if email_sent:
                        # Update last_sent
                        match_ids = [m.cat.id for m in result.matches]
                        db_manager.update_alert(
                            alert_id,
                            last_sent=datetime.now(),
                            last_match_ids=match_ids
                        )
                        print(f"✓ Email sent to {alert.user_email}")
                        return {
                            "success": True,
                            "alert_id": alert_id,
                            "message": f"Alert created and {len(result.matches)} matches sent to {alert.user_email}!"
                        }
                    else:
                        return {
                            "success": False,
                            "alert_id": alert_id,
                            "message": "Alert created but email failed to send"
                        }
                else:
                    return {
                        "success": False,
                        "alert_id": alert_id,
                        "message": "Email agent not enabled"
                    }
            else:
                print(f"No matches found")
                return {
                    "success": True,
                    "alert_id": alert_id,
                    "message": "Alert created but no matches found yet"
                }
        else:
            # For daily/weekly alerts
            return {
                "success": True,
                "alert_id": alert_id,
                "message": f"Alert created! You'll receive {alert.frequency} notifications at {alert.user_email}"
            }
            
    except Exception as e:
        print(f"Error creating alert: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "alert_id": None,
            "message": f"Error: {str(e)}"
        }


@app.function(
    image=image,
    schedule=modal.Cron("0 9 * * *"),  # Run daily at 9 AM UTC
    volumes={"/data": volume},
    secrets=secrets,
    timeout=600,
)
def daily_search_job() -> None:
    """Daily scheduled job to run cat searches for all daily alerts."""
    run_scheduled_searches.remote()


@app.function(
    image=image,
    schedule=modal.Cron("0 9 * * 1"),  # Run weekly on Mondays at 9 AM UTC
    volumes={"/data": volume},
    secrets=secrets,
    timeout=600,
)
def weekly_search_job() -> None:
    """Weekly scheduled job to run cat searches for all weekly alerts."""
    run_scheduled_searches.remote()


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=300,
)
def cleanup_old_data(days: int = 30) -> Dict[str, Any]:
    """
    Clean up old cat data from cache and vector database.
    
    Args:
        days: Number of days of data to keep (default: 30)
        
    Returns:
        Statistics dictionary with cleanup results
    """
    import sys
    print(f"[{datetime.now()}] Starting cleanup job (keeping last {days} days)")
    
    framework = TuxedoLinkFramework()
    stats = framework.cleanup_old_data(days)
    
    print(f"Cleanup complete: {stats}")
    print(f"[{datetime.now()}] Cleanup job completed")
    
    return stats


@app.function(
    image=image,
    schedule=modal.Cron("0 2 * * 0"),  # Run weekly on Sundays at 2 AM UTC
    volumes={"/data": volume},
    secrets=secrets,
    timeout=300,
)
def weekly_cleanup_job() -> None:
    """Weekly scheduled job to clean up old data (30+ days)."""
    cleanup_old_data.remote(30)


# For manual testing
@app.local_entrypoint()
def main() -> None:
    """Test the scheduled search locally for development."""
    run_scheduled_searches.remote()


if __name__ == "__main__":
    main()

