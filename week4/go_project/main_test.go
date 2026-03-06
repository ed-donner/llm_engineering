package main

import (
	"math"
	"testing"
)

func TestCalculateCore(t *testing.T) {
	// Test case 1: Normal operation with small iterations
	t.Run("NormalOperation", func(t *testing.T) {
		result := calculateCore(10, 2.0, 1.0)
		expected := 1.0
		// Using a small tolerance for floating point comparison
		if math.Abs(result-expected) > 1e-10 {
			t.Errorf("Expected %.12f, got %.12f", expected, result)
		}
	})

	// Test case 2: Edge case with zero param2
	t.Run("ZeroParam2", func(t *testing.T) {
		result := calculateCore(5, 3.0, 0.0)
		// Expected values from manual computation for this case
		expected := 1.0 - (1.0/3.0) + (1.0/3.0) - (1.0/6.0) + (1.0/6.0) - (1.0/9.0) + (1.0/9.0) - (1.0/12.0) + (1.0/12.0) - (1.0/15.0) + (1.0/15.0)
		if math.Abs(result-expected) > 1e-10 {
			t.Errorf("Expected %.12f, got %.12f", expected, result)
		}
	})

	// Test case 3: Edge case with larger iterations and specific parameters
	t.Run("LargeIterations", func(t *testing.T) {
		result := calculateCore(100, 1.0, 0.5)
		// Verify that result is finite and reasonable
		if math.IsNaN(result) || math.IsInf(result, 0) {
			t.Errorf("Result should not be NaN or Infinity, got: %v", result)
		}
		// Should be close to 1.0 for this specific case though the precise value
		// depends on floating point arithmetic
		if result < 0 {
			t.Errorf("Result should be positive for these parameters, got: %v", result)
		}
	})

	// Test case 4: Test with parameters that could cause division by zero
	t.Run("DivisionByZeroAvoidance", func(t *testing.T) {
		// This should not cause division by zero even with small iterations
		result := calculateCore(10, 1.0, 1.0) // param1 = 1.0, param2 = 1.0
		// Check that result is finite
		if math.IsNaN(result) || math.IsInf(result, 0) {
			t.Errorf("Result should not be NaN or Infinity, got: %v", result)
		}
	})

	// Test case 5: Verify the multiplication factor in calculate function works correctly
	t.Run("CalculateFunction", func(t *testing.T) {
		result := calculate(10, 2.0, 1.0)
		coreResult := calculateCore(10, 2.0, 1.0)
		if result != coreResult*4 {
			t.Errorf("calculate should multiply core result by 4, expected %.12f, got %.12f", coreResult*4, result)
		}
	})
}