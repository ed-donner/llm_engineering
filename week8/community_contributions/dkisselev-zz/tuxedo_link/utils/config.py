"""Configuration management for Tuxedo Link."""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


_config_cache: Dict[str, Any] = None


def load_config() -> Dict[str, Any]:
    """
    Load configuration from YAML with environment variable overrides.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    global _config_cache
    if _config_cache:
        return _config_cache
    
    # Determine config path - look for config.yaml, fallback to example
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config.yaml"
    
    if not config_path.exists():
        config_path = project_root / "config.example.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(
            "No config.yaml or config.example.yaml found. "
            "Please copy config.example.yaml to config.yaml and configure it."
        )
    
    # Load YAML
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables if present
    if 'EMAIL_PROVIDER' in os.environ:
        config['email']['provider'] = os.environ['EMAIL_PROVIDER']
    if 'DEPLOYMENT_MODE' in os.environ:
        config['deployment']['mode'] = os.environ['DEPLOYMENT_MODE']
    if 'MAILGUN_DOMAIN' in os.environ:
        config['mailgun']['domain'] = os.environ['MAILGUN_DOMAIN']
    
    _config_cache = config
    return config


def get_config() -> Dict[str, Any]:
    """
    Get current configuration.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    return load_config()


def is_production() -> bool:
    """
    Check if running in production mode.
    
    Returns:
        bool: True if production mode, False if local
    """
    return get_config()['deployment']['mode'] == 'production'


def get_db_path() -> str:
    """
    Get database path based on deployment mode.
    
    Returns:
        str: Path to database file
    """
    config = get_config()
    mode = config['deployment']['mode']
    return config['deployment'][mode]['db_path']


def get_vectordb_path() -> str:
    """
    Get vector database path based on deployment mode.
    
    Returns:
        str: Path to vector database directory
    """
    config = get_config()
    mode = config['deployment']['mode']
    return config['deployment'][mode]['vectordb_path']


def get_email_provider() -> str:
    """
    Get configured email provider.
    
    Returns:
        str: Email provider name (mailgun or sendgrid)
    """
    return get_config()['email']['provider']


def get_email_config() -> Dict[str, str]:
    """
    Get email configuration.
    
    Returns:
        Dict[str, str]: Email configuration (from_name, from_email)
    """
    return get_config()['email']


def get_mailgun_config() -> Dict[str, str]:
    """
    Get Mailgun configuration.
    
    Returns:
        Dict[str, str]: Mailgun configuration (domain)
    """
    return get_config()['mailgun']


def reload_config() -> None:
    """
    Force reload configuration from file.
    Useful for testing or when config changes.
    """
    global _config_cache
    _config_cache = None
    load_config()

