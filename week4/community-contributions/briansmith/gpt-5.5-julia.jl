using Printf

const ITERATIONS = 200_000_000
const PARAM1 = 4
const PARAM2 = 1

function calculate(iterations::Int, param1::Int, param2::Int)::Float64
    result = 1.0

    step = Float64(param1)
    neg = Float64(param1 - param2)
    pos = Float64(param1 + param2)

    o1 = step
    o2 = o1 + step
    o3 = o2 + step
    o4 = o2 + o2

    blocks = iterations ÷ 4
    k = 0

    while k < blocks
        a0 = 1.0 / neg
        b0 = 1.0 / pos
        a1 = 1.0 / (neg + o1)
        b1 = 1.0 / (pos + o1)
        a2 = 1.0 / (neg + o2)
        b2 = 1.0 / (pos + o2)
        a3 = 1.0 / (neg + o3)
        b3 = 1.0 / (pos + o3)

        result -= a0
        result += b0
        result -= a1
        result += b1
        result -= a2
        result += b2
        result -= a3
        result += b3

        neg += o4
        pos += o4
        k += 1
    end

    remaining = iterations - blocks * 4
    k = 0
    while k < remaining
        result -= 1.0 / neg
        result += 1.0 / pos
        neg += step
        pos += step
        k += 1
    end

    return result
end

calculate(0, PARAM1, PARAM2)

GC.enable(false)
start_time = time()
result = calculate(ITERATIONS, PARAM1, PARAM2) * 4.0
end_time = time()
GC.enable(true)

@printf("Result: %.12f\n", result)
@printf("Execution Time: %.6f seconds\n", end_time - start_time)