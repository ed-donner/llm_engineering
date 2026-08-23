#include <chrono>
#include <cstdio>

int main() {
    const long long iterations = 200'000'000LL;
    const long long param2 = 1;
    double result = 1.0;

    auto start = std::chrono::high_resolution_clock::now();
    for (long long i = 1; i <= iterations; ++i) {
        long long j = i << 2;                 // 4 * i
        double denom1 = double(j - param2);
        double denom2 = double(j + param2);
        result -= 1.0 / denom1;
        result += 1.0 / denom2;
    }
    result *= 4.0;
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> elapsed = end - start;
    printf("Result: %.12f\n", result);
    printf("Execution Time: %.6f seconds\n", elapsed.count());
    return 0;
}
