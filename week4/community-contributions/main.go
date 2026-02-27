package main

import (
	"fmt"
	"time"
)

func nextLCG(seed uint64) uint64 {
	const (
		a = uint64(1664525)
		c = uint64(1013904223)
		m = uint64(1) << 32
	)
	return (a*seed + c) % m
}

func maxSubarraySum(n int, seed uint64, minVal, maxVal int64) int64 {
	// Generate random numbers
	randomNumbers := make([]int64, n)
	state := seed
	diff := uint64(maxVal - minVal + 1)
	
	for i := 0; i < n; i++ {
		state = nextLCG(state)
		randomNumbers[i] = int64(state%diff) + minVal
	}

	// Kadane's algorithm
	var maxSum, currentSum int64
	maxSum = randomNumbers[0]
	currentSum = randomNumbers[0]
	
	for i := 1; i < n; i++ {
		if currentSum < 0 {
			currentSum = randomNumbers[i]
		} else {
			currentSum += randomNumbers[i]
		}
		if currentSum > maxSum {
			maxSum = currentSum
		}
	}
	return maxSum
}

func totalMaxSubarraySum(n int, initialSeed uint64, minVal, maxVal int64) int64 {
	var totalSum int64
	seed := initialSeed

	for i := 0; i < 20; i++ {
		seed = nextLCG(seed)
		totalSum += maxSubarraySum(n, seed, minVal, maxVal)
	}
	return totalSum
}

func main() {
	const (
		n           = 10000
		initialSeed = 42
		minVal      = -10
		maxVal      = 10
	)

	startTime := time.Now()
	result := totalMaxSubarraySum(n, initialSeed, minVal, maxVal)
	duration := time.Since(startTime)

	fmt.Printf("Total Maximum Subarray Sum (20 runs): %d\n", result)
	fmt.Printf("Execution Time: %.6f seconds\n", duration.Seconds())
}