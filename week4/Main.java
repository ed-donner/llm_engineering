public class Main {
    private static double calculate(int iterations, int param1, int param2) {
        double result = 1.0;
        for (int i = 1; i <= iterations; i++) {
            double j = i * param1 - param2;
            result -= (1.0 / j);
            j = i * param1 + param2;
            result += (1.0 / j);
        }
        return result;
    }

    public static void main(String[] args) {
        long startTime = System.nanoTime();
        double result = calculate(200_000_000, 4, 1) * 4;
        long endTime = System.nanoTime();

        System.out.printf("Result: %.12f%n", result);
        System.out.printf("Execution Time: %.6f seconds%n", (endTime - startTime) / 1e9);
    }
}