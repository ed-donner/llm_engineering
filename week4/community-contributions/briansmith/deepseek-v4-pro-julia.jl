
using Printf

function calculate(iterations::Int, param1::Int, param2::Int)
    result = 1.0
    for i in 1:iterations
        # Exact same operations as Python to ensure identical floating-point results
        result -= 1.0 / (i * param1 - param2)
        result += 1.0 / (i * param1 + param2)
    end
    return result
end

const ITER = 200_000_000
const PARAM1 = 4
const PARAM2 = 1

start = time()
result = calculate(ITER, PARAM1, PARAM2) * 4.0
elapsed = time() - start

@printf("Result: %.12f\n", result)
@printf("Execution Time: %.6f seconds\n", elapsed)
