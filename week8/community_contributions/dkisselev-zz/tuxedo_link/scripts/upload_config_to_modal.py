#!/usr/bin/env python
"""Upload config.yaml to Modal volume for remote configuration."""

import modal
import yaml
from pathlib import Path
import sys


def main():
    """Upload config.yaml to Modal volume."""
    # Load local config
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("❌ Error: config.yaml not found")
        print("Copy config.example.yaml to config.yaml and configure it")
        sys.exit(1)
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config.yaml: {e}")
        sys.exit(1)
    
    # Validate config
    if config['deployment']['mode'] != 'production':
        print("⚠️  Warning: config.yaml deployment mode is not set to 'production'")
    
    try:
        # Connect to Modal volume
        volume = modal.Volume.from_name("tuxedo-link-data", create_if_missing=True)
        
        # Remove old config if it exists
        try:
            volume.remove_file("/data/config.yaml")
            print("  Removed old config.yaml")
        except Exception:
            # File doesn't exist, that's fine
            pass
        
        # Upload new config
        with volume.batch_upload() as batch:
            batch.put_file(config_path, "/data/config.yaml")
        
        print("✓ Config uploaded to Modal volume")
        print(f"  Email provider: {config['email']['provider']}")
        print(f"  Deployment mode: {config['deployment']['mode']}")
        
    except Exception as e:
        print(f"❌ Error uploading config to Modal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

