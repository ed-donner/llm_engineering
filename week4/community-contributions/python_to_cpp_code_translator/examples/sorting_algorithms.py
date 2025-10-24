"""
Various sorting algorithms implemented in Python.
"""

import random
import time
from typing import List

def bubble_sort(arr: List[int]) -> List[int]:
    """Sort array using bubble sort algorithm."""
    n = len(arr)
    arr = arr.copy()  # Don't modify original array
    
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    
    return arr

def selection_sort(arr: List[int]) -> List[int]:
    """Sort array using selection sort algorithm."""
    n = len(arr)
    arr = arr.copy()
    
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    
    return arr

def insertion_sort(arr: List[int]) -> List[int]:
    """Sort array using insertion sort algorithm."""
    arr = arr.copy()
    
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    
    return arr

def quick_sort(arr: List[int]) -> List[int]:
    """Sort array using quick sort algorithm."""
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)

def merge_sort(arr: List[int]) -> List[int]:
    """Sort array using merge sort algorithm."""
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left: List[int], right: List[int]) -> List[int]:
    """Merge two sorted arrays."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def benchmark_sorting_algorithms():
    """Benchmark different sorting algorithms."""
    sizes = [100, 500, 1000, 2000]
    algorithms = {
        "Bubble Sort": bubble_sort,
        "Selection Sort": selection_sort,
        "Insertion Sort": insertion_sort,
        "Quick Sort": quick_sort,
        "Merge Sort": merge_sort
    }
    
    print("Sorting Algorithm Benchmark")
    print("=" * 50)
    
    for size in sizes:
        print(f"\nArray size: {size}")
        print("-" * 30)
        
        # Generate random array
        test_array = [random.randint(1, 1000) for _ in range(size)]
        
        for name, algorithm in algorithms.items():
            start_time = time.time()
            sorted_array = algorithm(test_array)
            end_time = time.time()
            
            # Verify sorting is correct
            is_sorted = all(sorted_array[i] <= sorted_array[i+1] for i in range(len(sorted_array)-1))
            
            print(f"{name:15}: {end_time - start_time:.4f}s {'✓' if is_sorted else '✗'}")

def main():
    """Main function to demonstrate sorting algorithms."""
    print("Sorting Algorithms Demo")
    print("=" * 30)
    
    # Test with small array
    test_array = [64, 34, 25, 12, 22, 11, 90]
    print(f"Original array: {test_array}")
    
    algorithms = {
        "Bubble Sort": bubble_sort,
        "Selection Sort": selection_sort,
        "Insertion Sort": insertion_sort,
        "Quick Sort": quick_sort,
        "Merge Sort": merge_sort
    }
    
    for name, algorithm in algorithms.items():
        sorted_array = algorithm(test_array)
        print(f"{name}: {sorted_array}")
    
    # Run benchmark
    print("\n" + "=" * 50)
    benchmark_sorting_algorithms()

if __name__ == "__main__":
    main()




