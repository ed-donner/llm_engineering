# Build first: python setup.py build_ext --inplace
import time
import math
import calculate_pi

# Original Python implementation
def py_leibniz_pi(iterations):
    result = 1.0
    for i in range(1, iterations + 1):
        j = i * 4 - 1
        result -= (1 / j)
        j = i * 4 + 1
        result += (1 / j)
    return result * 4

iters = 5_000_000

# Warm-up
calculate_pi.leibniz_pi(10)
py_leibniz_pi(10)

start = time.perf_counter()
res_c = calculate_pi.leibniz_pi(iters)
end = time.perf_counter()
ctime = end - start

start = time.perf_counter()
res_py = py_leibniz_pi(iters)
end = time.perf_counter()
pytime = end - start

print(f"Iterations: {iters}")
print(f"C extension result: {res_c}")
print(f"Python result:      {res_py}")
print(f"Absolute difference: {abs(res_c - res_py)}")
print(f"C extension time: {ctime:.6f} s")
print(f"Python time:      {pytime:.6f} s")
print(f"Speedup: {pytime/ctime if ctime > 0 else float('inf'):.2f}x")
