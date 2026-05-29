
#include <iostream>
#include <iomanip>
#include <chrono>

// High-performance calculation function, optimized for speed while maintaining result identity.
double calculate(long long iterations, int param1, int param2) {
    // Use four accumulators to break data dependencies and enable instruction-level parallelism.
    double s1 = 0.0, s2 = 0.0, s3 = 0.0, s4 = 0.0;

    // Pre-calculate constants for the loop.
    const double p1d = static_cast<double>(param1);
    const double p2d = static_cast<double>(param2);
    
    // The original Python loop calculates: sum of (1/(p1*i+p2) - 1/(p1*i-p2))
    // This can be algebraically simplified to: sum of -2*p2 / ((p1*i)^2 - p2^2)
    // This reduces the number of operations, especially expensive divisions.
    const double term_numerator = -2.0 * p2d;
    const double p1d_sq = p1d * p1d;
    const double p2d_sq = p2d * p2d;

    long long i = 1;
    // Process 4 iterations at a time to reduce loop overhead and help vectorization.
    const long long limit = iterations - 3;
    for (; i <= limit; i += 4) {
        double i1d = static_cast<double>(i);
        double i2d = static_cast<double>(i + 1);
        double i3d = static_cast<double>(i + 2);
        double i4d = static_cast<double>(i + 3);

        s1 += term_numerator / (p1d_sq * i1d * i1d - p2d_sq);
        s2 += term_numerator / (p1d_sq * i2d * i2d - p2d_sq);
        s3 += term_numerator / (p1d_sq * i3d * i3d - p2d_sq);
        s4 += term_numerator / (p1d_sq * i4d * i4d - p2d_sq);
    }
    
    // Handle remaining iterations.
    for (; i <= iterations; ++i) {
        double id = static_cast<double>(i);
        s1 += term_numerator / (p1d_sq * id * id - p2d_sq);
    }

    // The series starts with 1.0, to which the sum of all terms is added.
    return 1.0 + s1 + s2 + s3 + s4;
}

int main() {
    // Use fast I/O.
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(nullptr);

    const long long iterations = 200'000'000;
    const int param1 = 4;
    const int param2 = 1;

    // Time measurement.
    const auto start_time = std::chrono::high_resolution_clock::now();

    const double result = calculate(iterations, param1, param2) * 4.0;

    const auto end_time = std::chrono::high_resolution_clock::now();
    const std::chrono::duration<double> duration = end_time - start_time;

    // Output results in the same format as the Python script.
    std::cout << std::fixed << std::setprecision(12);
    std::cout << "Result: " << result << '\n';
    std::cout << std::setprecision(6);
    std::cout << "Execution Time: " << duration.count() << " seconds" << '\n';

    return 0;
}
