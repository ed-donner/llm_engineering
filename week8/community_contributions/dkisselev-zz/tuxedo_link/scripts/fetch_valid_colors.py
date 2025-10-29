#!/usr/bin/env python
"""Fetch and display valid colors and breeds from Petfinder API."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.petfinder_agent import PetfinderAgent

def main():
    """Fetch and display valid cat colors and breeds from Petfinder API."""
    print("=" * 70)
    print("Fetching Valid Cat Data from Petfinder API")
    print("=" * 70)
    print()
    
    try:
        # Initialize agent
        agent = PetfinderAgent()
        
        # Fetch colors
        print("📋 COLORS")
        print("-" * 70)
        colors = agent.get_valid_colors()
        
        print(f"✓ Found {len(colors)} valid colors:")
        print()
        
        for i, color in enumerate(colors, 1):
            print(f"  {i:2d}. {color}")
        
        print()
        print("=" * 70)
        print("Common user terms mapped to API colors:")
        print("  • 'tuxedo' → Black & White / Tuxedo")
        print("  • 'orange' → Orange / Red")
        print("  • 'gray' → Gray / Blue / Silver")
        print("  • 'orange tabby' → Tabby (Orange / Red)")
        print("  • 'calico' → Calico")
        print()
        
        # Fetch breeds
        print("=" * 70)
        print("📋 BREEDS")
        print("-" * 70)
        breeds = agent.get_valid_breeds()
        
        print(f"✓ Found {len(breeds)} valid breeds:")
        print()
        
        # Show first 30 breeds
        for i, breed in enumerate(breeds[:30], 1):
            print(f"  {i:2d}. {breed}")
        
        if len(breeds) > 30:
            print(f"  ... and {len(breeds) - 30} more breeds")
        
        print()
        print("=" * 70)
        print("These are the ONLY values accepted by Petfinder API")
        print("Use these exact values when making API requests")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

