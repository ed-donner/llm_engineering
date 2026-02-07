
#include <iostream>
#include <chrono>

double calculate(int iterations, int param1, int param2) {
    double result = 1.0;
    for (int i = 1; i <= iterations; ++i) {
        int j = i * param1 - param2;
        result -= 1.0 / j;
        j = i * param1 + param2;
        result += 1.0 / j;
    }
    return result;
}

int main() {
    auto start_time = std::chrono::high_resolution_clock::now();
    double result = calculate(200_000_000, 4, 1) * 4;
    auto end_time = std::chrono::high_resolution_clock::now();

    std::cout << "Result: " << std::setprecision(12) << result << std::endl;
    std::cout << "Execution Time: " 
              << std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time).count() / 1'000'000.0
              << " seconds" << std::endl;

    return 0;
}
