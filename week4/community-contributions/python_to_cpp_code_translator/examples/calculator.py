"""
Simple calculator class with history tracking.
"""

import math
from typing import List, Union

class Calculator:
    """A simple calculator with history tracking."""
    
    def __init__(self):
        """Initialize calculator with empty history."""
        self.history: List[str] = []
        self.memory: float = 0.0
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def power(self, base: float, exponent: float) -> float:
        """Calculate base raised to the power of exponent."""
        result = base ** exponent
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result
    
    def square_root(self, number: float) -> float:
        """Calculate square root of a number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        result = math.sqrt(number)
        self.history.append(f"√{number} = {result}")
        return result
    
    def factorial(self, n: int) -> int:
        """Calculate factorial of n."""
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        if n == 0 or n == 1:
            return 1
        
        result = 1
        for i in range(2, n + 1):
            result *= i
        
        self.history.append(f"{n}! = {result}")
        return result
    
    def memory_store(self, value: float) -> None:
        """Store value in memory."""
        self.memory = value
        self.history.append(f"Memory stored: {value}")
    
    def memory_recall(self) -> float:
        """Recall value from memory."""
        self.history.append(f"Memory recalled: {self.memory}")
        return self.memory
    
    def memory_clear(self) -> None:
        """Clear memory."""
        self.memory = 0.0
        self.history.append("Memory cleared")
    
    def get_history(self) -> List[str]:
        """Get calculation history."""
        return self.history.copy()
    
    def clear_history(self) -> None:
        """Clear calculation history."""
        self.history.clear()
    
    def get_last_result(self) -> Union[float, None]:
        """Get the result of the last calculation."""
        if not self.history:
            return None
        
        last_entry = self.history[-1]
        # Extract result from history entry
        if "=" in last_entry:
            return float(last_entry.split("=")[-1].strip())
        return None

class ScientificCalculator(Calculator):
    """Extended calculator with scientific functions."""
    
    def sine(self, angle: float) -> float:
        """Calculate sine of angle in radians."""
        result = math.sin(angle)
        self.history.append(f"sin({angle}) = {result}")
        return result
    
    def cosine(self, angle: float) -> float:
        """Calculate cosine of angle in radians."""
        result = math.cos(angle)
        self.history.append(f"cos({angle}) = {result}")
        return result
    
    def tangent(self, angle: float) -> float:
        """Calculate tangent of angle in radians."""
        result = math.tan(angle)
        self.history.append(f"tan({angle}) = {result}")
        return result
    
    def logarithm(self, number: float, base: float = math.e) -> float:
        """Calculate logarithm of number with given base."""
        if number <= 0:
            raise ValueError("Logarithm is not defined for non-positive numbers")
        if base <= 0 or base == 1:
            raise ValueError("Logarithm base must be positive and not equal to 1")
        
        result = math.log(number, base)
        self.history.append(f"log_{base}({number}) = {result}")
        return result
    
    def degrees_to_radians(self, degrees: float) -> float:
        """Convert degrees to radians."""
        return degrees * math.pi / 180
    
    def radians_to_degrees(self, radians: float) -> float:
        """Convert radians to degrees."""
        return radians * 180 / math.pi

def main():
    """Main function to demonstrate calculator functionality."""
    print("Calculator Demo")
    print("=" * 30)
    
    # Basic calculator
    calc = Calculator()
    
    print("Basic Calculator Operations:")
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")
    print(f"2 ^ 8 = {calc.power(2, 8)}")
    print(f"√64 = {calc.square_root(64)}")
    print(f"5! = {calc.factorial(5)}")
    
    print(f"\nCalculation History:")
    for entry in calc.get_history():
        print(f"  {entry}")
    
    # Scientific calculator
    print("\n" + "=" * 30)
    print("Scientific Calculator Operations:")
    
    sci_calc = ScientificCalculator()
    
    # Convert degrees to radians for trigonometric functions
    angle_deg = 45
    angle_rad = sci_calc.degrees_to_radians(angle_deg)
    
    print(f"sin({angle_deg}°) = {sci_calc.sine(angle_rad):.4f}")
    print(f"cos({angle_deg}°) = {sci_calc.cosine(angle_rad):.4f}")
    print(f"tan({angle_deg}°) = {sci_calc.tangent(angle_rad):.4f}")
    print(f"ln(10) = {sci_calc.logarithm(10):.4f}")
    print(f"log₁₀(100) = {sci_calc.logarithm(100, 10):.4f}")
    
    print(f"\nScientific Calculator History:")
    for entry in sci_calc.get_history():
        print(f"  {entry}")

if __name__ == "__main__":
    main()




