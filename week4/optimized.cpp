// Gemini conversion failed, using Claude conversion

#include <iostream>
#include <chrono>
#include <limits>
#include <vector>
#include <iomanip>

class LCG {
private:
    uint32_t value;
    static constexpr uint32_t a = 1664525;
    static constexpr uint32_t c = 1013904223;
    
public:
    LCG(uint32_t seed) : value(seed) {}
    
    uint32_t next() {
        value = a * value + c;
        return value;
    }
};

int64_t max_subarray_sum(int n, uint32_t seed, int min_val, int max_val) {
    LCG lcg_gen(seed);
    int range = max_val - min_val + 1;
    
    // Generate random numbers
    std::vector<int> random_numbers(n);
    for (int i = 0; i < n; ++i) {
        random_numbers[i] = lcg_gen.next() % range + min_val;
    }
    
    // Kadane's algorithm for maximum subarray sum
    int64_t max_sum = std::numeric_limits<int64_t>::min();
    int64_t current_sum = 0;
    
    for (int i = 0; i < n; ++i) {
        current_sum = std::max(static_cast<int64_t>(random_numbers[i]), 
                              current_sum + random_numbers[i]);
        max_sum = std::max(max_sum, current_sum);
    }
    
    // Handle all negative numbers case
    if (max_sum < 0) {
        max_sum = *std::max_element(random_numbers.begin(), random_numbers.end());
    }
    
    return max_sum;
}

int64_t total_max_subarray_sum(int n, uint32_t initial_seed, int min_val, int max_val) {
    int64_t total_sum = 0;
    LCG lcg_gen(initial_seed);
    
    for (int i = 0; i < 20; ++i) {
        uint32_t seed = lcg_gen.next();
        total_sum += max_subarray_sum(n, seed, min_val, max_val);
    }
    
    return total_sum;
}

int main() {
    int n = 10000;
    uint32_t initial_seed = 42;
    int min_val = -10;
    int max_val = 10;
    
    auto start_time = std::chrono::high_resolution_clock::now();
    int64_t result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    auto end_time = std::chrono::high_resolution_clock::now();
    
    std::chrono::duration<double> execution_time = end_time - start_time;
    
    std::cout << "Total Maximum Subarray Sum (20 runs): " << result << std::endl;
    std::cout << "Execution Time: " << std::fixed << std::setprecision(6) 
              << execution_time.count() << " seconds" << std::endl;
    
    return 0;
}