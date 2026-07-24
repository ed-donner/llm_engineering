#include <iostream>
#include <iomanip>
#include <chrono>
#include <cstdint>

static inline double calculate(uint64_t iterations, int param1, int param2) {
    double result = 1.0;
    const double p1 = static_cast<double>(param1);
    const double p2 = static_cast<double>(param2);
    double fi = p1;
    for (uint64_t i = 1; i <= iterations; ++i, fi += p1) {
        double j = fi - p2;
        result -= 1.0 / j;
        j = fi + p2;
        result += 1.0 / j;
    }
    return result;
}

int main() {
    using namespace std::chrono;
    auto start_time = high_resolution_clock::now();
    double result = calculate(100000000ULL, 4, 1) * 4.0;
    auto end_time = high_resolution_clock::now();
    double elapsed = duration<double>(end_time - start_time).count();

    std::cout.setf(std::ios::fixed);
    std::cout << "Result: " << std::setprecision(12) << result << '\n';
    std::cout << "Execution Time: " << std::setprecision(6) << elapsed << " seconds\n";
    return 0;
}