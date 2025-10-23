#!/usr/bin/env python3

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import and run
from main import main

if __name__ == "__main__":
    main()