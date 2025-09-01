
import time
import zz_my_module

def python_hello_world():
    print("Hello, World!")

start = time.time()
python_hello_world()
end = time.time()
print(f"Python function execution time: {end - start:.6f} seconds")

start = time.time()
zz_my_module.hello_world()
end = time.time()
print(f"C extension execution time: {end - start:.6f} seconds")
