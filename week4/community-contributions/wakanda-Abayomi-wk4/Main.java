import java.io.*;

public class Main {
    public static void main(String[] args) {
        long iterations = 200_000_000L;
        double param1 = 4.0;
        double param2 = 1.0;

        long start = System.nanoTime();
        double result = calculate(iterations, param1, param2) * 4.0;
        long end = System.nanoTime();

        double elapsed = (end - start) / 1_000_000_000.0;

        System.out.printf("Result: %.12f%n", result);
        System.out.printf("Execution Time: %.6f seconds%n", elapsed);
    }

    private static double calculate(long iterations, double param1, double param2) {
        double result = 1.0;
        for (long i = 1; i <= iterations; i++) {
            double j = i * param1 - param2;
            result -= 1.0 / j;
            j = i * param1 + param2;
            result += 1.0 / j;
        }
        return result;
    }
}