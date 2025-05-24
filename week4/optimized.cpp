#include <iostream>
#include <vector>
#include <cstdint>
#include <chrono>

// LCG parameters
const uint64_t a = 1664525;
const uint64_t c = 1013904223;
const uint64_t m = 1ULL << 32;

// LCG function
class LCG {
public:
    LCG(uint64_t seed) : value(seed) {}
    uint64_t next() {
        value = (a * value + c) % m;
        return value;
    }
    
private:
    uint64_t value;
};

// Finds the maximum subarray sum using the Kadane's algorithm
uint64_t max_subarray_sum(int n, uint64_t seed, int min_val, int max_val) {
    LCG lcg_gen(seed);
    std::vector<int> random_numbers(n);
    
    for (int i = 0; i < n; ++i) {
        random_numbers[i] = static_cast<int>(lcg_gen.next() % (max_val - min_val + 1) + min_val);
    }

    int64_t max_sum = INT64_MIN;
    int64_t current_sum = 0;
    
    for (int i = 0; i < n; ++i) {
        current_sum += random_numbers[i];
        if (current_sum > max_sum) {
            max_sum = current_sum;
        }
        if (current_sum < 0) {
            current_sum = 0;
        }
    }
    
    return max_sum;
}

// Aggregates the maximum subarray sums over 20 runs
uint64_t total_max_subarray_sum(int n, uint64_t initial_seed, int min_val, int max_val) {
    uint64_t total_sum = 0;
    LCG lcg_gen(initial_seed);
    
    for (int i = 0; i < 20; ++i) {
        total_sum += max_subarray_sum(n, lcg_gen.next(), min_val, max_val);
    }
    
    return total_sum;
}

int main() {
    // Parameters
    int n = 10000;
    uint64_t initial_seed = 42;
    int min_val = -10;
    int max_val = 10;
    
    // Timing the function
    auto start_time = std::chrono::high_resolution_clock::now();
    uint64_t result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    auto end_time = std::chrono::high_resolution_clock::now();
    
    std::chrono::duration<double> elapsed = end_time - start_time;
    
    std::cout << "Total Maximum Subarray Sum (20 runs): " << result << std::endl;
    std::cout << "Execution Time: " << std::fixed << elapsed.count() << " seconds" << std::endl;
    
    return 0;
}
