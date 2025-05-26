
#include <iostream>
#include <iomanip>
#include <chrono>

double calculate(long iterations, int param1, int param2) {
    double result = 1.0;
    for (long i = 1; i <= iterations; ++i) {
        double j = i * param1 - param2;
        result -= (1/j);
        j = i * param1 + param2;
        result += (1/j);
    }
    return result;
}

int main() {
    auto start_time = std::chrono::high_resolution_clock::now();
    double result = calculate(100000000, 4, 1) * 4;
    auto end_time = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> elapsed = end_time - start_time;
    std::cout << std::fixed << std::setprecision(12);
    std::cout << "Result: " << result << std::endl;
    std::cout << "Execution Time: " << elapsed.count() << " seconds" << std::endl;

    return 0;
}
