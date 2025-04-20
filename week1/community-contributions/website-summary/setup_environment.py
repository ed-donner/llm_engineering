def ensure_dependencies():
    """Check for required packages and install them if not found."""
    import importlib
    import subprocess
    import sys

    # Define required packages
    required_packages = {
        'requests': 'requests',
        'beautifulsoup4': 'bs4',
        'selenium': 'selenium',
        'openai': 'openai',
        'webdriver-manager': 'webdriver_manager',
        # Add any other required packages here
    }

    missing_packages = []

    # Check which packages are missing
    for package_name, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"✓ {package_name} is already installed")
        except ImportError:
            missing_packages.append(package_name)
            print(f"✗ {package_name} needs to be installed")

    # Install missing packages
    if missing_packages:
        print("\nInstalling missing packages...")
        for package in missing_packages:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"Successfully installed {package}")
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}")

    # Verify all packages are now installed
    all_installed = True
    for package_name, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            all_installed = False
            print(f"⚠️ {package_name} installation failed")

    return all_installed