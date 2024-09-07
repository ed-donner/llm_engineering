#include <iostream>
#include <random>
#include <chrono>
#include <iomanip>

// Function to generate random numbers using Mersenne Twister
std::mt19937 gen(42);

// Function to calculate maximum subarray sum
int max_subarray_sum(int n, int min_val, int max_val) {
    std::uniform_int_distribution<> dis(min_val, max_val);
    int max_sum = std::numeric_limits<int>::min();
    int current_sum = 0;
    for (int i = 0; i < n; ++i) {
        current_sum += dis(gen);
        if (current_sum > max_sum) {
            max_sum = current_sum;
        }
        if (current_sum < 0) {
            current_sum = 0;
        }
    }
    return max_sum;
}

// Function to calculate total maximum subarray sum
int total_max_subarray_sum(int n, int initial_seed, int min_val, int max_val) {
    gen.seed(initial_seed);
    int total_sum = 0;
    for (int i = 0; i < 20; ++i) {
        total_sum += max_subarray_sum(n, min_val, max_val);
    }
    return total_sum;
}

int main() {
    int n = 10000;         // Number of random numbers
    int initial_seed = 42; // Initial seed for the Mersenne Twister
    int min_val = -10;     // Minimum value of random numbers
    int max_val = 10;      // Maximum value of random numbers

    // Timing the function
    auto start_time = std::chrono::high_resolution_clock::now();
    int result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    auto end_time = std::chrono::high_resolution_clock::now();

    std::cout << "Total Maximum Subarray Sum (20 runs): " << result << std::endl;
    std::cout << "Execution Time: " << std::setprecision(6) << std::fixed << std::chrono::duration<double>(end_time - start_time).count() << " seconds" << std::endl;

    return 0;
}