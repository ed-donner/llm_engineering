
function calculate(iterations::Int, param1::Int, param2::Int)
    result = 1.0
    @inbounds @simd for i in 1:iterations
        j1 = i * param1 - param2
        j2 = i * param1 + param2
        result += (1.0/j2) - (1.0/j1)
    end
    return result
end

calculate(100, 4, 1)  # warmup

start_time = time()
result = calculate(200_000_000, 4, 1) * 4
end_time = time()

println("Result: $(round(result; digits=12))")
@printf_str = string("Execution Time: ", round(end_time - start_time; digits=6), " seconds")
println(@printf_str)
