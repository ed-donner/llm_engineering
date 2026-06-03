import time

# Original Python code

def lcg(seed, a=1664525, c=1013904223, m=2**32):
    value = seed
    while True:
        value = (a * value + c) % m
        yield value

def max_subarray_sum_py(n, seed, min_val, max_val):
    lcg_gen = lcg(seed)
    random_numbers = [next(lcg_gen) % (max_val - min_val + 1) + min_val for _ in range(n)]
    max_sum = float('-inf')
    for i in range(n):
        current_sum = 0
        for j in range(i, n):
            current_sum += random_numbers[j]
            if current_sum > max_sum:
                max_sum = current_sum
    return max_sum

def total_max_subarray_sum_py(n, initial_seed, min_val, max_val):
    total_sum = 0
    lcg_gen = lcg(initial_seed)
    for _ in range(20):
        seed = next(lcg_gen)
        total_sum += max_subarray_sum_py(n, seed, min_val, max_val)
    return total_sum

# Build and import extension (after running: python setup.py build && install or develop)
import python_hard as ext

# Example parameters
n = 600
initial_seed = 12345678901234567890
min_val = -1000
max_val = 1000

# Time Python
t0 = time.perf_counter()
py_res1 = max_subarray_sum_py(n, (initial_seed * 1664525 + 1013904223) % (2**32), min_val, max_val)
t1 = time.perf_counter()
py_time1 = t1 - t0

# Time C extension
t0 = time.perf_counter()
ext_res1 = ext.max_subarray_sum(n, (initial_seed * 1664525 + 1013904223) % (2**32), min_val, max_val)
t1 = time.perf_counter()
ext_time1 = t1 - t0

print('max_subarray_sum equality:', py_res1 == ext_res1)
print('Python time:', py_time1)
print('C ext time:', ext_time1)

# Total over 20 seeds
t0 = time.perf_counter()
py_res2 = total_max_subarray_sum_py(n, initial_seed, min_val, max_val)
t1 = time.perf_counter()
py_time2 = t1 - t0

t0 = time.perf_counter()
ext_res2 = ext.total_max_subarray_sum(n, initial_seed, min_val, max_val)
t1 = time.perf_counter()
ext_time2 = t1 - t0

print('total_max_subarray_sum equality:', py_res2 == ext_res2)
print('Python total time:', py_time2)
print('C ext total time:', ext_time2)
