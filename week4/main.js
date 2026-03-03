script
function calculate(iterations, param1, param2) {
    let result = 1.0;
    for (let i = 1; i <= iterations; i++) {
        let j = i * param1 - param2;
        result -= 1 / j;
        j = i * param1 + param2;
        result += 1 / j;
    }
    return result;
}

const startTime = performance.now();
const result = calculate(200_000_000, 4, 1) * 4;
const endTime = performance.now();

console.log(`Result: ${result.toFixed(12)}`);
console.log(`Execution Time: ${((endTime - startTime) / 1000).toFixed(6)} seconds`);