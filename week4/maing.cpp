
#include <iostream>
#include <iomanip>
#include <chrono>

// Function to perform the calculation
double calculate(int iterations, double param1, double param2) {
    double result = 1.0;
    // Using a for loop for iterations
    for (int i = 1; i <= iterations; ++i) {
        // Calculate j for subtraction
        double j_sub = static_cast<double>(i) * param1 - param2;
        // Calculate j for addition
        double j_add = static_cast<double>(i) * param1 + param2;
        
        // Avoid division by zero, although with the given parameters it's unlikely
        if (j_sub != 0) {
            result -= (1.0 / j_sub);
        }
        if (j_add != 0) {
            result += (1.0 / j_add);
        }
    }
    return result;
}

int main() {
    // Record start time
    auto start_time = std::chrono::high_resolution_clock::now();

    // Define parameters
    int iterations = 200000000;
    double param1 = 4.0;
    double param2 = 1.0;

    // Perform calculation and multiply by 4
    double final_result = calculate(iterations, param1, param2) * 4.0;

    // Record end time
    auto end_time = std::chrono::high_resolution_clock::now();
    // Calculate duration
    std::chrono::duration<double> elapsed_time = end_time - start_time;

    // Print the result with specified precision
    std::cout << std::fixed << std::setprecision(12) << "Result: " << final_result << std::endl;
    // Print the execution time with specified precision
    std::cout << std::fixed << std::setprecision(6) << "Execution Time: " << elapsed_time.count() << " seconds" << std::endl;

    return 0;
}
