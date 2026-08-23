"""
Classification Tester for Banking Intent Model
Evaluates model accuracy on intent classification
"""

import matplotlib.pyplot as plt
from collections import Counter
from banking_intents import get_intent

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


class ClassifierTester:
    """Test framework for classification models"""
    
    def __init__(self, predictor, data, title=None, size=100):
        self.predictor = predictor
        self.data = data
        self.title = title or predictor.__name__.replace("_", " ").title()
        self.size = min(size, len(data))
        self.predictions = []
        self.actuals = []
        self.correct = 0
        self.incorrect = 0
    
    def run_datapoint(self, i):
        """Test a single example"""
        item = self.data[i]
        
        # Get prediction
        predicted_intent = self.predictor(item)
        actual_intent = get_intent(item['label'])
        
        # Check if correct
        is_correct = predicted_intent == actual_intent
        
        if is_correct:
            self.correct += 1
            color = GREEN
            status = "✓"
        else:
            self.incorrect += 1
            color = RED
            status = "✗"
        
        self.predictions.append(predicted_intent)
        self.actuals.append(actual_intent)
        
        # Print result
        query = item['text'][:60] + "..." if len(item['text']) > 60 else item['text']
        print(f"{color}{status} {i+1}: {query}")
        print(f"   Predicted: {predicted_intent} | Actual: {actual_intent}{RESET}")
    
    def chart(self):
        """Visualize top confusion pairs"""
        # Find misclassifications
        errors = {}
        for pred, actual in zip(self.predictions, self.actuals):
            if pred != actual:
                pair = f"{actual} → {pred}"
                errors[pair] = errors.get(pair, 0) + 1
        
        if not errors:
            print("\n🎉 Perfect accuracy - no confusion to plot!")
            return
        
        # Plot top 10 confusions
        top_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_errors:
            labels = [pair for pair, _ in top_errors]
            counts = [count for _, count in top_errors]
            
            plt.figure(figsize=(12, 6))
            plt.barh(labels, counts, color='coral')
            plt.xlabel('Count')
            plt.title('Top 10 Confusion Pairs (Actual → Predicted)')
            plt.tight_layout()
            plt.show()
    
    def report(self):
        """Print final metrics and chart"""
        accuracy = (self.correct / self.size) * 100
        
        print("\n" + "="*70)
        print(f"MODEL: {self.title}")
        print(f"TESTED: {self.size} examples")
        print(f"CORRECT: {self.correct} ({accuracy:.1f}%)")
        print(f"INCORRECT: {self.incorrect}")
        print("="*70)
        
        # Show most common errors
        if self.incorrect > 0:
            print("\nMost Common Errors:")
            error_pairs = [(self.actuals[i], self.predictions[i]) 
                          for i in range(len(self.actuals)) 
                          if self.actuals[i] != self.predictions[i]]
            error_counts = Counter(error_pairs).most_common(5)
            
            for (actual, pred), count in error_counts:
                print(f"  {actual} → {pred}: {count} times")
        
        # Chart
        self.chart()
        
        return accuracy
    
    def run(self):
        """Run the complete evaluation"""
        print(f"Testing {self.title} on {self.size} examples...\n")
        
        for i in range(self.size):
            self.run_datapoint(i)
        
        return self.report()
    
    @classmethod
    def test(cls, function, data, size=100):
        """Convenience method to test a predictor function"""
        return cls(function, data, size=size).run()

