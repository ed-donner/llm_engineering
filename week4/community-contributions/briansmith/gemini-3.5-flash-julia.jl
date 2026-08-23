
using Printf

# Highly optimized calculation using Float64 arithmetic and avoiding 
# integer-to-float conversions inside the loop.
function calculate(iterations::Int, param1::Int, param2::Int)
    result = 1.0
    j1 = Float64(param1 - param2)
    j2 = Float64(param1 + param2)
    step = Float64(param1)
    
    # @fastmath allows the compiler to perform SIMD vectorization 
    # and pipelining of the floating-point divisions.
    @inbounds @fastmath for _ in 1:iterations
        result -= 1.0 / j1
        result += 1.0 / j2
        j1 += step
        j2 += step
    end
    return result
end

function main()
    start_time = time()
    result = calculate(200_000_000, 4, 1) * 4
    end_time = time()
    
    @printf("Result: %.12f\n", result)
    @printf("Execution Time: %.6f seconds\n", end_time - start_time)
end

main()
