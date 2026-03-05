#include <cstdio>
#include <chrono>

int main() {
    // Total iterations as in the Python code
    constexpr unsigned int ITER = 200000000;

    double sum = 1.0;

    auto start = std::chrono::high_resolution_clock::now();

    // Unrolled loop: preserve per-iteration order to match Python behavior
    for (unsigned int i = 1; i <= ITER; i += 4) {
        double base = 4.0 * static_cast<double>(i);

        // i
        sum -= 1.0 / (base - 1.0);
        sum += 1.0 / (base + 1.0);

        // i+1
        unsigned int i1 = i + 1;
        if (i1 <= ITER) {
            sum -= 1.0 / (base + 3.0);
            sum += 1.0 / (base + 5.0);
        }

        // i+2
        unsigned int i2 = i + 2;
        if (i2 <= ITER) {
            sum -= 1.0 / (base + 7.0);
            sum += 1.0 / (base + 9.0);
        }

        // i+3
        unsigned int i3 = i + 3;
        if (i3 <= ITER) {
            sum -= 1.0 / (base + 11.0);
            sum += 1.0 / (base + 13.0);
        }
    }

    double result = sum * 4.0;

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;

    printf("Result: %.12f\n", result);
    printf("Execution Time: %.6f seconds\n", duration.count());

    return 0;
}