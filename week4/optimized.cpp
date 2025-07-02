// Gemini conversion failed, using Claude conversion

#include <iostream>
#include <iomanip>
#include <chrono>
#include <limits>
#include <cstdint>

class LCG {
private:
    uint64_t value;
    static constexpr uint64_t a = 1664525;
    static constexpr uint64_t c = 1013904223;
    static constexpr uint64_t m = 4294967296ULL; // 2^32
    
public:
    LCG(uint64_t seed) : value(seed) {}
    
    uint64_t next() {
        value = (a * value + c) % m;
        return value;
    }
};

int64_t max_subarray_sum(int n, uint64_t seed, int min_val, int max_val) {
    LCG lcg_gen(seed);
    int range = max_val - min_val + 1;
    
    // Generate all random numbers at once
    int* random_numbers = new int[n];
    for (int i = 0; i < n; i++) {
        random_numbers[i] = lcg_gen.next() % range + min_val;
    }
    
    // Kadane's algorithm for maximum subarray sum
    int64_t max_sum = std::numeric_limits<int64_t>::min();
    int64_t current_sum = 0;
    
    for (int i = 0; i < n; i++) {
        current_sum = std::max(static_cast<int64_t>(random_numbers[i]), 
                              current_sum + random_numbers[i]);
        max_sum = std::max(max_sum, current_sum);
    }
    
    delete[] random_numbers;
    return max_sum;
}

int64_t total_max_subarray_sum(int n, uint64_t initial_seed, int min_val, int max_val) {
    int64_t total_sum = 0;
    LCG lcg_gen(initial_seed);
    
    for (int i = 0; i < 20; i++) {
        uint64_t seed = lcg_gen.next();
        total_sum += max_subarray_sum(n, seed, min_val, max_val);
    }
    
    return total_sum;
}

int main() {
    int n = 10000;
    uint64_t initial_seed = 42;
    int min_val = -10;
    int max_val = 10;
    
    auto start_time = std::chrono::high_resolution_clock::now();
    int64_t result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    auto end_time = std::chrono::high_resolution_clock::now();
    
    std::chrono::duration<double> diff = end_time - start_time;
    
    std::cout << "Total Maximum Subarray Sum (20 runs): " << result << std::endl;
    std::cout << "Execution Time: " << std::fixed << std::setprecision(6) 
              << diff.count() << " seconds" << std::endl;
    
    return 0;
}