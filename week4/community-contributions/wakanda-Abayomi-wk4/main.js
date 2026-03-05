"use strict";

const iterations = 200000000;
const a = 4.0;
const b = 1.0;

// Digamma function implementation (stable for positive arguments)
function digamma(x) {
  let result = 0.0;
  while (x < 6.0) {
    result -= 1.0 / x;
    x += 1.0;
  }

  const x2 = x * x;
  const x4 = x2 * x2;
  const x6 = x4 * x2;
  const x8 = x4 * x4;
  const x10 = x8 * x2;

  // Asymptotic expansion for large x:
  // psi(x) ≈ ln(x) - 1/(2x) - 1/(12x^2) + 1/(120x^4) - 1/(252x^6) + 1/(240x^8) - 5/(660x^10)
  const expansion = Math.log(x)
    - 0.5 / x
    - 1.0 / (12.0 * x2)
    + 1.0 / (120.0 * x4)
    - 1.0 / (252.0 * x6)
    + 1.0 / (240.0 * x8)
    - 5.0 / (660.0 * x10);

  return result + expansion;
}

function finalResult(N, aVal, bVal) {
  const c = bVal / aVal;
  const delta = digamma(N + 1 - c) - digamma(N + 1 + c) + digamma(1 + c) - digamma(1 - c);
  return 4.0 * (1.0 - delta / aVal);
}

// Time the computation (high-resolution)
const hrstart = process.hrtime();
const result = finalResult(iterations, a, b);
const diff = process.hrtime(hrstart);
const elapsed = diff[0] + diff[1] / 1e9;

console.log(`Result: ${result.toFixed(12)}`);
console.log(`Execution Time: ${elapsed.toFixed(6)} seconds`);