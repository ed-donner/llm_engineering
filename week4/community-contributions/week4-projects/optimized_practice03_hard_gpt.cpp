#include <iostream>
#include <cstdint>
#include <chrono>
#include <iomanip>
#include <string>
#include <algorithm>

static inline uint32_t lcg_next(uint32_t& v) {
    v = v * 1664525u + 1013904223u; // modulo 2^32 via uint32_t wrap
    return v;
}

static std::string int128_to_string(__int128 x) {
    if (x == 0) return "0";
    bool neg = x < 0;
    if (neg) x = -x;
    std::string s;
    while (x > 0) {
        int d = (int)(x % 10);
        s.push_back(char('0' + d));
        x /= 10;
    }
    if (neg) s.push_back('-');
    std::reverse(s.begin(), s.end());
    return s;
}

static __int128 max_subarray_sum(std::size_t n, uint32_t seed, long long min_val, long long max_val) {
    uint32_t state = seed;
    unsigned __int128 urange = (unsigned __int128)((__int128)max_val - (__int128)min_val + 1);
    __int128 best = 0, current = 0;
    bool first = true;
    for (std::size_t i = 0; i < n; ++i) {
        uint32_t rnd = lcg_next(state);
        unsigned __int128 rem = (unsigned __int128)rnd % urange;
        __int128 val = (__int128)rem + (__int128)min_val;
        if (first) {
            current = best = val;
            first = false;
        } else {
            __int128 sum = current + val;
            current = (sum > val) ? sum : val;
            if (current > best) best = current;
        }
    }
    return best;
}

static __int128 total_max_subarray_sum(std::size_t n, uint32_t initial_seed, long long min_val, long long max_val) {
    __int128 total = 0;
    uint32_t seed_state = initial_seed;
    for (int k = 0; k < 20; ++k) {
        uint32_t run_seed = lcg_next(seed_state);
        total += max_subarray_sum(n, run_seed, min_val, max_val);
    }
    return total;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    std::size_t n = 10000;
    uint32_t initial_seed = 42u;
    long long min_val = -10;
    long long max_val = 10;

    auto start = std::chrono::high_resolution_clock::now();
    __int128 result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> elapsed = end - start;

    std::cout << "Total Maximum Subarray Sum (20 runs): " << int128_to_string(result) << '\n';
    std::cout << "Execution Time: " << std::fixed << std::setprecision(6) << elapsed.count() << " seconds\n";
    return 0;
}