#include <iostream>
#include <iomanip>
#include <chrono>
#include <cmath>

static inline double fast_result() {
    // Exact identity for the Python computation:
    // 4 * calculate(N, 4, 1) = psi(N + 1.25) - psi(N + 0.75) + pi
    // Use asymptotic expansion of digamma difference for large N:
    constexpr double N = 200000000.0;
    const double b = N + 0.75;           // large
    const double a = b + 0.5;            // a = N + 1.25
    // ln(a/b) computed stably
    double res = std::log1p(0.5 / b);
    const double inva = 1.0 / a, invb = 1.0 / b;

    // Bernoulli series terms for digamma:
    res -= 0.5 * (inva - invb);
    const double inva2 = inva * inva, invb2 = invb * invb;
    res -= (1.0 / 12.0) * (inva2 - invb2);
    const double inva4 = inva2 * inva2, invb4 = invb2 * invb2;
    res += (1.0 / 120.0) * (inva4 - invb4);
    const double inva6 = inva4 * inva2, invb6 = invb4 * invb2;
    res -= (1.0 / 252.0) * (inva6 - invb6);
    const double inva8 = inva4 * inva4, invb8 = invb4 * invb4;
    res += (1.0 / 240.0) * (inva8 - invb8);
    const double inva10 = inva8 * inva2, invb10 = invb8 * invb2;
    res -= (1.0 / 132.0) * (inva10 - invb10);
    const double inva12 = inva10 * inva2, invb12 = invb10 * invb2;
    res += (691.0 / 32760.0) * (inva12 - invb12); // overkill but essentially free

    const double pi = std::acos(-1.0);
    return res + pi;
}

int main() {
    using clock = std::chrono::high_resolution_clock;
    auto start = clock::now();
    double result = fast_result();
    auto end = clock::now();
    double elapsed = std::chrono::duration<double>(end - start).count();

    std::cout.setf(std::ios::fixed);
    std::cout << "Result: " << std::setprecision(12) << result << "\n";
    std::cout << "Execution Time: " << std::setprecision(6) << elapsed << " seconds\n";
    return 0;
}