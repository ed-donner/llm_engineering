"""
Complete Modal API for Tuxedo Link
All application logic runs on Modal in production mode
"""

import modal
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from cat_adoption_framework import TuxedoLinkFramework
from models.cats import CatProfile, AdoptionAlert
from database.manager import DatabaseManager
from agents.profile_agent import ProfileAgent
from agents.email_agent import EmailAgent
from agents.email_providers.factory import get_email_provider

# Modal app and configuration
app = modal.App("tuxedo-link-api")

# Create Modal volume for persistent data
volume = modal.Volume.from_name("tuxedo-link-data", create_if_missing=True)

# Reference secrets
secrets = [modal.Secret.from_name("tuxedo-link-secrets")]

# Get project directory
project_dir = Path(__file__).parent

# Modal image with all dependencies and project files
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "openai",
        "chromadb", 
        "requests",
        "sentence-transformers==2.5.1", 
        "transformers==4.38.0",  
        "Pillow",
        "python-dotenv",
        "pydantic",
        "geopy",
        "pyyaml",
        "python-levenshtein",
        "open-clip-torch==2.24.0", 
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


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=600,
    cpu=2.0,
    memory=4096,
)
def search_cats(profile_dict: Dict[str, Any], use_cache: bool = False) -> Dict[str, Any]:
    """
    Main search function - runs all agents and returns matches.
    
    This is the primary API endpoint for cat searches in production mode.
    
    Args:
        profile_dict: CatProfile as dictionary
        use_cache: Whether to use cached data
        
    Returns:
        Dict with matches, stats, and search metadata
    """
    print(f"[{datetime.now()}] Modal API: Starting cat search")
    print(f"Profile location: {profile_dict.get('user_location', 'Not specified')}")
    print(f"Cache mode: {use_cache}")
    
    try:
        # Initialize framework
        framework = TuxedoLinkFramework()
        
        # Reconstruct profile
        profile = CatProfile(**profile_dict)
        
        # Run search
        result = framework.search(profile, use_cache=use_cache)
        
        print(f"Found {len(result.matches)} matches")
        print(f"Duplicates removed: {result.duplicates_removed}")
        print(f"Sources: {len(result.sources_queried)}")
        
        # Convert to serializable dict
        return {
            "success": True,
            "matches": [
                {
                    "cat": m.cat.model_dump(),
                    "match_score": m.match_score,
                    "vector_similarity": m.vector_similarity,
                    "attribute_match_score": m.attribute_match_score,
                    "explanation": m.explanation,
                    "matching_attributes": m.matching_attributes,
                    "missing_attributes": m.missing_attributes,
                }
                for m in result.matches
            ],
            "total_found": result.total_found,
            "duplicates_removed": result.duplicates_removed,
            "sources_queried": result.sources_queried,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        print(f"Error in search_cats: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "matches": [],
            "total_found": 0,
            "duplicates_removed": 0,
            "sources_queried": [],
        }


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=300,
)
def create_alert_and_notify(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create alert in Modal DB and send immediate notification if needed.
    
    Args:
        alert_data: AdoptionAlert as dictionary
        
    Returns:
        Dict with success status, alert_id, and message
    """
    
    from cat_adoption_framework import TuxedoLinkFramework
    from database.manager import DatabaseManager
    from models.cats import AdoptionAlert
    from agents.email_agent import EmailAgent
    from agents.email_providers.factory import get_email_provider
    
    print(f"[{datetime.now()}] Modal API: Creating alert")
    
    try:
        # Initialize components
        db_manager = DatabaseManager("/data/tuxedo_link.db")
        
        # Reconstruct alert
        alert = AdoptionAlert(**alert_data)
        print(f"Alert for: {alert.user_email}, frequency: {alert.frequency}")
        
        # Save to Modal DB
        alert_id = db_manager.create_alert(alert)
        print(f"Alert created with ID: {alert_id}")
        
        alert.id = alert_id
        
        # If immediate, send notification now
        if alert.frequency == "immediately":
            print("Processing immediate notification...")
            framework = TuxedoLinkFramework()
            email_provider = get_email_provider()
            email_agent = EmailAgent(email_provider)
            
            # Run search
            result = framework.search(alert.profile, use_cache=False)
            
            if result.matches:
                print(f"Found {len(result.matches)} matches")
                
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
                    "success": True,
                    "alert_id": alert_id,
                    "message": "Alert created but no matches found yet"
                }
        else:
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
    volumes={"/data": volume},
    secrets=secrets,
    timeout=60,
)
def get_alerts(email: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get alerts from Modal DB.
    
    Args:
        email: Optional email filter
        
    Returns:
        List of alert dictionaries
    """
    
    from database.manager import DatabaseManager
    
    try:
        db_manager = DatabaseManager("/data/tuxedo_link.db")
        
        if email:
            alerts = db_manager.get_alerts_by_email(email)
        else:
            alerts = db_manager.get_all_alerts()
        
        return [alert.dict() for alert in alerts]
        
    except Exception as e:
        print(f"Error getting alerts: {e}")
        return []


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=60,
)
def update_alert(alert_id: int, active: Optional[bool] = None) -> bool:
    """
    Update alert in Modal DB.
    
    Args:
        alert_id: Alert ID
        active: New active status
        
    Returns:
        True if successful
    """
    
    from database.manager import DatabaseManager
    
    try:
        db_manager = DatabaseManager("/data/tuxedo_link.db")
        db_manager.update_alert(alert_id, active=active)
        return True
    except Exception as e:
        print(f"Error updating alert: {e}")
        return False


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=60,
)
def delete_alert(alert_id: int) -> bool:
    """
    Delete alert from Modal DB.
    
    Args:
        alert_id: Alert ID
        
    Returns:
        True if successful
    """
    
    from database.manager import DatabaseManager
    
    try:
        db_manager = DatabaseManager("/data/tuxedo_link.db")
        db_manager.delete_alert(alert_id)
        return True
    except Exception as e:
        print(f"Error deleting alert: {e}")
        return False


@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=secrets,
    timeout=120,
)
def extract_profile(user_input: str) -> Dict[str, Any]:
    """
    Extract cat profile from natural language using LLM.
    
    Args:
        user_input: User's description of desired cat
        
    Returns:
        CatProfile as dictionary
    """
    
    from agents.profile_agent import ProfileAgent
    
    print(f"[{datetime.now()}] Modal API: Extracting profile")
    
    try:
        agent = ProfileAgent()
        conversation = [{"role": "user", "content": user_input}]
        profile = agent.extract_profile(conversation)
        
        return {
            "success": True,
            "profile": profile.dict()
        }
        
    except Exception as e:
        print(f"Error extracting profile: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "profile": None
        }


# Health check
@app.function(image=image, timeout=10)
def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "tuxedo-link-api"
    }

