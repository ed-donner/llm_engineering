#include <iostream>
#include <vector>
#include <chrono>
#include <limits>
#include <iomanip>

using namespace std;
using namespace chrono;

class LCG {
private:
    uint64_t value;
    static const uint64_t a = 1664525;
    static const uint64_t c = 1013904223;
    static const uint64_t m = 1ULL << 32;

public:
    LCG(uint64_t seed) : value(seed) {}

    uint64_t next() {
        value = (a * value + c) % m;
        return value;
    }
};

int64_t max_subarray_sum(int n, uint64_t seed, int min_val, int max_val) {
    LCG lcg(seed);
    vector<int64_t> random_numbers(n);
    for (int i = 0; i < n; ++i) {
        random_numbers[i] = lcg.next() % (max_val - min_val + 1) + min_val;
    }

    int64_t max_sum = numeric_limits<int64_t>::min();
    int64_t current_sum = 0;
    int64_t min_sum = 0;

    for (int i = 0; i < n; ++i) {
        current_sum += random_numbers[i];
        max_sum = max(max_sum, current_sum - min_sum);
        min_sum = min(min_sum, current_sum);
    }

    return max_sum;
}

int64_t total_max_subarray_sum(int n, uint64_t initial_seed, int min_val, int max_val) {
    int64_t total_sum = 0;
    LCG lcg(initial_seed);
    for (int i = 0; i < 20; ++i) {
        uint64_t seed = lcg.next();
        total_sum += max_subarray_sum(n, seed, min_val, max_val);
    }
    return total_sum;
}

int main() {
    const int n = 10000;
    const uint64_t initial_seed = 42;
    const int min_val = -10;
    const int max_val = 10;

    auto start_time = high_resolution_clock::now();
    int64_t result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    auto end_time = high_resolution_clock::now();

    auto duration = duration_cast<microseconds>(end_time - start_time);

    cout << "Total Maximum Subarray Sum (20 runs): " << result << endl;
    cout << "Execution Time: " << fixed << setprecision(6) << duration.count() / 1e6 << " seconds" << endl;

    return 0;
}