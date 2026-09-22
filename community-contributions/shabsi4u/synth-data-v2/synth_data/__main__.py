"""
CLI entry point for Synthetic Data Generator.

Runs the Streamlit application.

Usage:
    python -m synth_data
"""

import sys
import subprocess


def main():
    """Launch the Streamlit application."""
    try:
        # Run streamlit with the app.py file
        subprocess.run([
            sys.executable,
            "-m", "streamlit",
            "run",
            "synth_data/ui/app.py",
            "--server.headless", "true"
        ], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
