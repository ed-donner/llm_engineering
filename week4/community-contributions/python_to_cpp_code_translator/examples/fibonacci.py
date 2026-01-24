"""
Fibonacci sequence implementation in Python.
"""

def fibonacci(n):
    """Calculate the nth Fibonacci number using recursion."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def fibonacci_iterative(n):
    """Calculate the nth Fibonacci number using iteration."""
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def fibonacci_sequence(count):
    """Generate a sequence of Fibonacci numbers."""
    sequence = []
    for i in range(count):
        sequence.append(fibonacci(i))
    return sequence

def main():
    """Main function to demonstrate Fibonacci calculations."""
    print("Fibonacci Sequence Demo")
    print("=" * 30)
    
    # Calculate first 10 Fibonacci numbers
    for i in range(10):
        result = fibonacci(i)
        print(f"fibonacci({i}) = {result}")
    
    print("\nFirst 15 Fibonacci numbers:")
    sequence = fibonacci_sequence(15)
    print(sequence)
    
    # Performance comparison
    import time
    
    n = 30
    print(f"\nPerformance comparison for fibonacci({n}):")
    
    start_time = time.time()
    recursive_result = fibonacci(n)
    recursive_time = time.time() - start_time
    
    start_time = time.time()
    iterative_result = fibonacci_iterative(n)
    iterative_time = time.time() - start_time
    
    print(f"Recursive: {recursive_result} (took {recursive_time:.4f}s)")
    print(f"Iterative: {iterative_result} (took {iterative_time:.4f}s)")

if __name__ == "__main__":
    main()




