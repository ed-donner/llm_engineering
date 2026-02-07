#include <iostream>
#include <unistd.h>

const long double param1 = 4.0;
const long double param2 = 1.0;

long double calculate(long double iterations) {
    long double result = 1.0;
    for (int i = 1; i <= static_cast<int>(iterations); ++i) {
        long double j = i * param1 - param2;
        result -= (1.0 / j);
        j = i * param1 + param2;
        result += (1.0 / j);
    }
    return result * param1;
}

int main() {
    // Avoid precision issues by using long double arithmetic
    std::cout.precision(18);

    auto start_time = std::chrono::high_resolution_clock::now();

    long int iterations = 200000000;
    auto result = calculate(iterations);

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time).count() / 1000.0;

    // Print and display result in a human-readable format
    std::cout << "Result: " << result << std::endl;
    std::cout << "Execution Time: " << duration / 60.0 << ".00 seconds" << std::endl;

    return 0;
}