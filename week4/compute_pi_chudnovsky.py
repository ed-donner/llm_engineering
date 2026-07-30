import time
import gmpy2
from gmpy2 import mpz

def pi_chudnovsky_bs(digits):
    """
    Computes Pi to `digits` decimal places using Chudnovsky's algorithm
    with Binary Splitting implemented via gmpy2.
    """
    # Each term in the Chudnovsky series yields ~14.1816474627254776 digits
    DIGITS_PER_TERM = 14.1816474627254776
    N = int(digits / DIGITS_PER_TERM) + 1

    # Chudnovsky Constants
    C = 640320
    C3_OVER_24 = C**3 // 24

    def bs(a, b):
        """Binary Splitting recursive function operating purely on large integers."""
        if b - a == 1:
            if a == 0:
                P = mpz(1)
                Q = mpz(1)
                T = mpz(13591409)
            else:
                P = mpz((6 * a - 5) * (2 * a - 1) * (6 * a - 1))
                Q = mpz(a**3 * C3_OVER_24)
                T = P * (13591409 + 545140134 * a)
                if a & 1:
                    T = -T
            return P, Q, T

        # Midpoint for divide-and-conquer binary split
        m = (a + b) // 2
        P_a, Q_a, T_a = bs(a, m)
        P_b, Q_b, T_b = bs(m, b)

        P = P_a * P_b
        Q = Q_a * Q_b
        T = Q_b * T_a + P_a * T_b
        return P, Q, T

    print(f"Starting calculation of Pi to {digits:,} decimal places...")
    start_time = time.time()

    # Step 1: Run binary splitting (pure integer math)
    print("1/3: Computing integer series sum via Binary Splitting...")
    P, Q, T = bs(0, N)

    # Step 2: Final floating point square root and division
    print("2/3: Computing final floating-point operations...")
    bits = int(digits * 3.321928094887362) + 100
    gmpy2.get_context().precision = bits

    # Formula: pi = (Q * 426880 * sqrt(10005)) / T
    numerator = Q * 426880 * gmpy2.sqrt(gmpy2.mpfr(10005))
    pi = numerator / T

    calc_time = time.time() - start_time
    print(f"Math finished in {calc_time:.2f} seconds!")

    # Step 3: Format string conversion
    print("3/3: Formatting integer string representation...")
    fmt_start = time.time()
    pi_str = f"{pi:.{digits}f}"
    fmt_time = time.time() - fmt_start

    return pi_str, calc_time, fmt_time

if __name__ == "__main__":
    target_digits = 100_000_000
    
    pi_str, cpu_time, fmt_time = pi_chudnovsky_bs(target_digits)

    print(f"\n--- Benchmark Summary ---")
    print(f"Calculation time: {cpu_time:.2f}s")
    print(f"String format time: {fmt_time:.2f}s")
    print(f"Total time:       {cpu_time + fmt_time:.2f}s")
    print(f"First 50 digits:  {pi_str[:52]}")
    print(f"Last 10 digits:   {pi_str[-10:]}")