"""
Simple test/demo script for the decision analysis modules.
Run this to verify the architecture works without Streamlit.
"""
from bn_decision_maker import DecisionBN
from bn_decision_maker.examples.predefined_cases import PREDEFINED_CASES

# Example BN data (minimal test case)
test_bn_data = {
    "variables": [
        {"name": "CoinFlip", "states": ["heads", "tails"]},
        {"name": "Outcome", "states": ["win", "lose"]}
    ],
    "edges": [
        ["CoinFlip", "Outcome"]
    ],
    "cpts": {
        "CoinFlip": {
            "heads": 0.5,
            "tails": 0.5
        },
        "Outcome": {
            "parents": ["CoinFlip"],
            "table": {
                "heads": {"win": 0.9, "lose": 0.1},
                "tails": {"win": 0.3, "lose": 0.7}
            }
        }
    }
}

def test_basic_bn():
    """Test basic BN construction and queries."""
    print("=" * 60)
    print("Testing DecisionBN class")
    print("=" * 60)
    
    # Create BN
    bn = DecisionBN(test_bn_data, "TestBN")
    print(f"✓ Created BN with {len(bn.get_variables())} variables")
    
    # Test marginal
    marginal = bn.get_marginal("Outcome")
    print(f"\n✓ Marginal P(Outcome):")
    for state, prob in marginal.items():
        print(f"  {state}: {prob:.4f}")
    
    # Test posterior with evidence
    evidence = {"CoinFlip": "heads"}
    posterior = bn.get_posterior(["Outcome"], evidence)["Outcome"]
    print(f"\n✓ Posterior P(Outcome | CoinFlip=heads):")
    for state, prob in posterior.items():
        print(f"  {state}: {prob:.4f}")
    
    # Test expected utilities
    utilities = {
        "Bet": {"win": 10, "lose": -5},
        "Don't Bet": {"win": 0, "lose": 0}
    }
    eus = bn.compute_expected_utilities("Outcome", utilities, evidence)
    print(f"\n✓ Expected utilities given evidence:")
    for action, eu in eus.items():
        print(f"  {action}: {eu:.2f}")
    
    # optimal_policy = bn.get_optimal_policy()
    # print(optimal_policy)
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)

def show_predefined_cases():
    """Display available predefined cases."""
    print("\n" + "=" * 60)
    print("Available Predefined Cases")
    print("=" * 60)
    
    for i, (name, description) in enumerate(PREDEFINED_CASES.items(), 1):
        print(f"\n{i}. {name}")
        print(f"   {description[:100]}...")

if __name__ == "__main__":
    test_basic_bn()
    show_predefined_cases()
    
    print("\n" + "=" * 60)
    print("To run the web app:")
    print("  streamlit run app.py")
    print("=" * 60)
