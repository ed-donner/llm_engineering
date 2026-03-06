
#include <iostream>
#include <iomanip>
#include <chrono>

int main() {
    auto start = std::chrono::high_resolution_clock::now();
    
    double result = 1.0;
    const long long iterations = 200000000;
    const int param1 = 4;
    const int param2 = 1;
    
    for (long long i = 1; i <= iterations; ++i) {
        long long j = i * param1 - param2;
        result -= 1.0 / j;
        j = i * param1 + param2;
        result += 1.0 / j;
    }
    
    result *= 4.0;
    
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> duration = end - start;
    
    std::cout << std::fixed << std::setprecision(12);
    std::cout << "Result: " << result << '\n';
    std::cout << std::fixed << std::setprecision(6);
    std::cout << "Execution Time: " << duration.count() << " seconds\n";
    
    return 0;
}
