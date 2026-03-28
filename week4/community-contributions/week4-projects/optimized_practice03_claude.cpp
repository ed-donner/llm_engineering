
#include <iostream>
#include <iomanip>
#include <chrono>

double calculate(long long iterations, int param1, int param2) {
    double result = 1.0;
    const double inv_param1 = 1.0 / param1;
    
    for (long long i = 1; i <= iterations; ++i) {
        const double base = i * param1;
        const double j1 = base - param2;
        const double j2 = base + param2;
        result += (1.0 / j2) - (1.0 / j1);
    }
    return result;
}

int main() {
    auto start_time = std::chrono::high_resolution_clock::now();
    double result = calculate(100000000LL, 4, 1) * 4.0;
    auto end_time = std::chrono::high_resolution_clock::now();
    
    auto duration = std::chrono::duration<double>(end_time - start_time);
    
    std::cout << std::fixed << std::setprecision(12);
    std::cout << "Result: " << result << std::endl;
    std::cout << std::setprecision(6);
    std::cout << "Execution Time: " << duration.count() << " seconds" << std::endl;
    
    return 0;
}
