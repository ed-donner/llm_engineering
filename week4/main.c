#include <stdio.h>
#include <time.h>

double calculate(int iterations, int param1, int param2) {
    double result = 1.0;
    for (int i = 1; i <= iterations; i++) {
        double j = i * param1 - param2;
        result -= (1.0 / j);
        j = i * param1 + param2;
        result += (1.0 / j);
    }
    return result;
}

int main() {
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    double result = calculate(200000000, 4, 1) * 4.0;
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    double time_spent = (end.tv_sec - start.tv_sec) + 
                        (end.tv_nsec - start.tv_nsec) / 1000000000.0;
    
    printf("Result: %.12f\n", result);
    printf("Execution Time: %.6f seconds\n", time_spent);
    
    return 0;
}