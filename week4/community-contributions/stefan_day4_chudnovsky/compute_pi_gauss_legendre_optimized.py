import time
import gmpy2

def compute_pi_gmpy2(digits):
    # Calculate required bits for the target decimal digits (log2(10) ≈ 3.3219)
    # Plus safety margin
    bits = int(digits * 3.321928094887362) + 50
    gmpy2.get_context().precision = bits

    a = gmpy2.mpfr(1)
    b = gmpy2.sqrt(gmpy2.mpfr("0.5"))
    t = gmpy2.mpfr("0.25")
    p = 1
    
    half = gmpy2.mpfr("0.5")

    print(f"Starting calculation of Pi to {digits:,} decimal places using gmpy2...")
    start_time = time.time()

    # 19 iterations yield over 500,000 digits of precision
    for _ in range(20):
        a_next = (a + b) * half
        b = gmpy2.sqrt(a * b)
        
        a_diff = a - a_next
        t -= p * (a_diff * a_diff)
        
        a = a_next
        p *= 2

    a_plus_b = a + b
    pi = (a_plus_b * a_plus_b) / (4 * t)

    duration = time.time() - start_time
    
    # Format to exact target decimal places
    pi_str = f"{pi:.{digits}f}"
    
    return pi_str, duration

if __name__ == "__main__":
    target_digits = 1000000
    pi_str, cpu_time = compute_pi_gmpy2(target_digits)

    print(f"Finished in {cpu_time:.5f} seconds!")
    print(f"First 50 digits: {pi_str[:52]}")
    print(f"Last 10 digits:  {pi_str[-10:]}")