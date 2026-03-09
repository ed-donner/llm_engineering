#include <cstdio>
#include <cstdint>
#include <chrono>

static inline double calculate(uint64_t iterations, double param1, double param2) noexcept {
    double result = 1.0;
    const double A = param1;
    const double p2sq = param2 * param2;
    const double c = -2.0 * param2;

    uint64_t i = 1;
    if (iterations >= 16) {
        const uint64_t unroll_end = iterations - 15;
        double res = result;
        for (; i <= unroll_end; i += 16) {
            double t0  = (double)i * A;
            double t1  = t0 + A;
            double t2  = t1 + A;
            double t3  = t2 + A;
            double t4  = t3 + A;
            double t5  = t4 + A;
            double t6  = t5 + A;
            double t7  = t6 + A;
            double t8  = t7 + A;
            double t9  = t8 + A;
            double t10 = t9 + A;
            double t11 = t10 + A;
            double t12 = t11 + A;
            double t13 = t12 + A;
            double t14 = t13 + A;
            double t15 = t14 + A;

            res += c / (t0  * t0  - p2sq);
            res += c / (t1  * t1  - p2sq);
            res += c / (t2  * t2  - p2sq);
            res += c / (t3  * t3  - p2sq);
            res += c / (t4  * t4  - p2sq);
            res += c / (t5  * t5  - p2sq);
            res += c / (t6  * t6  - p2sq);
            res += c / (t7  * t7  - p2sq);
            res += c / (t8  * t8  - p2sq);
            res += c / (t9  * t9  - p2sq);
            res += c / (t10 * t10 - p2sq);
            res += c / (t11 * t11 - p2sq);
            res += c / (t12 * t12 - p2sq);
            res += c / (t13 * t13 - p2sq);
            res += c / (t14 * t14 - p2sq);
            res += c / (t15 * t15 - p2sq);
        }
        result = res;
    }
    for (; i <= iterations; ++i) {
        double t = (double)i * A;
        result += c / (t * t - p2sq);
    }
    return result;
}

int main() {
    using clock = std::chrono::high_resolution_clock;
    auto start_time = clock::now();

    double result = calculate(200000000ULL, 4.0, 1.0) * 4.0;

    auto end_time = clock::now();
    double elapsed = std::chrono::duration<double>(end_time - start_time).count();

    std::printf("Result: %.12f\n", result);
    std::printf("Execution Time: %.6f seconds\n", elapsed);
    return 0;
}