package main

import (
	"fmt"
	"time"
)

// calculateCore performs the core computation logic
func calculateCore(iterations int, param1, param2 float64) float64 {
	result := 1.0
	for i := 1; i <= iterations; i++ {
		j := float64(i) * param1 - param2
		result -= 1 / j
		j = float64(i) * param1 + param2
		result += 1 / j
	}
	return result
}

func calculate(iterations int, param1, param2 float64) float64 {
	result := calculateCore(iterations, param1, param2)
	return result * 4
}

func main() {
	startTime := time.Now()
	result := calculate(100_000_000, 4, 1)
	endTime := time.Now()

	fmt.Printf("Result: %.12f\n", result)
	fmt.Printf("Execution Time: %.6f seconds\n", endTime.Sub(startTime).Seconds())
}