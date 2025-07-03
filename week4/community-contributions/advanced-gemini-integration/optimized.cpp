#include <iostream>
#include <iomanip>
#include <vector>
#include <limits>
#include <chrono>

int64_t max_subarray_sum(int n, uint32_t seed, int min_val, int max_val) {
    const uint32_t a = 1664525;
    const uint32_t c = 1013904223;
    const uint32_t m = 4294967296U; // 2^32
    
    std::vector<int> random_numbers;
    random_numbers.reserve(n);
    
    uint32_t value = seed;
    int range = max_val - min_val + 1;
    
    for (int i = 0; i < n; ++i) {
        value = (static_cast<uint64_t>(a) * value + c) % m;
        random_numbers.push_back(value % range + min_val);
    }
    
    int64_t max_sum = std::numeric_limits<int64_t>::min();
    
    for (int i = 0; i < n; ++i) {
        int64_t current_sum = 0;
        for (int j = i; j < n; ++j) {
            current_sum += random_numbers[j];
            if (current_sum > max_sum) {
                max_sum = current_sum;
            }
        }
    }
    
    return max_sum;
}

int main() {
    const int n = 10000;
    const uint32_t initial_seed = 42;
    const int min_val = -10;
    const int max_val = 10;
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    int64_t total_sum = 0;
    uint32_t seed = initial_seed;
    const uint32_t a = 1664525;
    const uint32_t c = 1013904223;
    const uint32_t m = 4294967296U;
    
    for (int i = 0; i < 20; ++i) {
        seed = (static_cast<uint64_t>(a) * seed + c) % m;
        total_sum += max_subarray_sum(n, seed, min_val, max_val);
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end_time - start_time;
    
    std::cout << "Total Maximum Subarray Sum (20 runs): " << total_sum << std::endl;
    std::cout << "Execution Time: " << std::fixed << std::setprecision(6) 
              << duration.count() << " seconds" << std::endl;
    
    return 0;
}