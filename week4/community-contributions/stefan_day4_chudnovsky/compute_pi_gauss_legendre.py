import time
from decimal import Decimal, getcontext

def compute_pi_gauss_legendre(digits):
    # Set precision with a safety margin
    getcontext().prec = digits + 10

    # Initialize starting values (using Decimal)
    a = Decimal(1)
    b = 1 / Decimal(2).sqrt()
    t = Decimal(1) / Decimal(4)
    p = Decimal(1)

    print(f"Starting calculation of Pi to {digits} decimal places...")
    start_time = time.time()

    # Only ~14 iterations are needed for 10,000 digits
    # (thanks to quadratic convergence)!
    # Each iteration requires CPU-intensive square root and division operations.
    for i in range(18):
        a_next = (a + b) / 2
        b = (a * b).sqrt()
        t -= p * (a - a_next) ** 2
        a = a_next
        p *= 2

    # Final step to approximate Pi
    pi = ((a + b) ** 2) / (4 * t)

    duration = time.time() - start_time
    getcontext().prec = digits  # Trim to the exact target precision
    return +pi, duration

# Run the calculation
pi_val, cpu_time = compute_pi_gauss_legendre(200000)

print(f"Finished in {cpu_time:.2f} seconds!")
print(f"First 50 digits: {str(pi_val)[:52]}")
print(f"Last 10 digits: {str(pi_val)[-10:]}")
# print(f"Pi: {str(pi_val)}")