"""Configuration settings for the CodeXchange AI application."""

# Model configurations
OPENAI_MODEL = "gpt-4o-mini"
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
DEEPSEEK_MODEL = "deepseek-chat"
GEMINI_MODEL = "gemini-1.5-flash"
GROQ_MODEL = "llama3-70b-8192"

# Supported languages and models
SUPPORTED_LANGUAGES = ["Python", "Julia", "JavaScript", "Go", "Java", "C++", "Ruby", "Swift", "Rust", "C#", "TypeScript", "R", "Perl", "Lua", "PHP", "Kotlin", "SQL"]
MODELS = ["GPT", "Claude", "Gemini", "DeepSeek", "GROQ"]

# Language mapping for syntax highlighting
LANGUAGE_MAPPING = {
    "Python": "python",
    "JavaScript": "javascript",
    "Java": "python",
    "C++": "cpp",
    "Julia": "python",
    "Go": "c",
    "Ruby": "python",
    "Swift": "python",
    "Rust": "python",
    "C#": "python",
    "TypeScript": "typescript",
    "R": "r",
    "Perl": "python",
    "Lua": "python",
    "PHP": "python",
    "Kotlin": "python",
    "SQL": "sql"
}

# File extensions for each language
LANGUAGE_FILE_EXTENSIONS = {
    "Python": ".py",
    "JavaScript": ".js",
    "Java": ".java",
    "C++": ".cpp",
    "Julia": ".jl",
    "Go": ".go",
    "Ruby": ".rb",
    "Swift": ".swift",
    "Rust": ".rs",
    "C#": ".cs",
    "TypeScript": ".ts",
    "R": ".r",
    "Perl": ".pl",
    "Lua": ".lua",
    "PHP": ".php",
    "Kotlin": ".kt",
    "SQL": ".sql"
}

# Documentation styles available for each language
DOCUMENT_STYLES = {
    "Python": [
        {"value": "standard", "label": "Standard (PEP 257)"},
        {"value": "google", "label": "Google Style"},
        {"value": "numpy", "label": "NumPy Style"}
    ],
    "Julia": [
        {"value": "standard", "label": "Standard"},
        {"value": "docsystem", "label": "Documenter.jl Style"}
    ],
    "JavaScript": [
        {"value": "standard", "label": "Standard"},
        {"value": "jsdoc", "label": "JSDoc Style"},
        {"value": "tsdoc", "label": "TSDoc Style"}
    ],
    "Go": [
        {"value": "standard", "label": "Standard"},
        {"value": "godoc", "label": "GoDoc Style"}
    ],
    "Java": [
        {"value": "standard", "label": "Standard"},
        {"value": "javadoc", "label": "JavaDoc Style"}
    ],
    "C++": [
        {"value": "standard", "label": "Standard"},
        {"value": "doxygen", "label": "Doxygen Style"}
    ],
    "Ruby": [
        {"value": "standard", "label": "Standard"},
        {"value": "yard", "label": "YARD Style"},
        {"value": "rdoc", "label": "RDoc Style"}
    ],
    "Swift": [
        {"value": "standard", "label": "Standard"},
        {"value": "markup", "label": "Swift Markup"}
    ],
    "Rust": [
        {"value": "standard", "label": "Standard"},
        {"value": "rustdoc", "label": "Rustdoc Style"}
    ],
    "C#": [
        {"value": "standard", "label": "Standard"},
        {"value": "xmldoc", "label": "XML Documentation"}
    ],
    "TypeScript": [
        {"value": "standard", "label": "Standard"},
        {"value": "tsdoc", "label": "TSDoc Style"}
    ],
    "R": [
        {"value": "standard", "label": "Standard"},
        {"value": "roxygen2", "label": "Roxygen2 Style"}
    ],
    "Perl": [
        {"value": "standard", "label": "Standard"},
        {"value": "pod", "label": "POD Style"}
    ],
    "Lua": [
        {"value": "standard", "label": "Standard"},
        {"value": "ldoc", "label": "LDoc Style"}
    ],
    "PHP": [
        {"value": "standard", "label": "Standard"},
        {"value": "phpdoc", "label": "PHPDoc Style"}
    ],
    "Kotlin": [
        {"value": "standard", "label": "Standard"},
        {"value": "kdoc", "label": "KDoc Style"}
    ],
    "SQL": [
        {"value": "standard", "label": "Standard"},
        {"value": "block", "label": "Block Comment Style"}
    ]
}

# Predefined code snippets for the UI
PREDEFINED_SNIPPETS = {
    "Python Code Simple" : """ 
    import time

def calculate(iterations, param1, param2):
    result = 1.0
    for i in range(1, iterations+1):
        j = i * param1 - param2
        result -= (1/j)
        j = i * param1 + param2
        result += (1/j)
    return result

start_time = time.time()
result = calculate(100_000_000, 4, 1) * 4
end_time = time.time()

print(f"Result: {result:.12f}")
print(f"Execution Time: {(end_time - start_time):.6f} seconds")
    """,
    "Python Code": """import time
import random
from typing import List, Tuple

class LCG:
    #Linear Congruential Generator
    def __init__(self, seed: int):
        self.value = seed
        self.a = 1664525
        self.c = 1013904223
        self.m = 2**32
    
    def next(self) -> int:
        # Generate next random number
        self.value = (self.a * self.value + self.c) % self.m
        return self.value

def max_subarray_sum(n: int, seed: int, min_val: int, max_val: int) -> int:
    # Calculate maximum subarray sum for array of random numbers
    lcg = LCG(seed)
    random_numbers = []
    
    # Generate random numbers
    for _ in range(n):
        random_numbers.append((lcg.next() % (max_val - min_val + 1)) + min_val)
    
    max_sum = float('-inf')
    
    # Calculate max subarray sum
    for i in range(n):
        current_sum = 0
        for j in range(i, n):
            current_sum += random_numbers[j]
            if current_sum > max_sum:
                max_sum = current_sum
    
    return max_sum

def total_max_subarray_sum(n: int, initial_seed: int, min_val: int, max_val: int) -> int:
    # Calculate total of maximum subarray sums over 20 iterations
    total_sum = 0
    lcg = LCG(initial_seed)
    
    for _ in range(20):
        seed = lcg.next()
        total_sum += max_subarray_sum(n, seed, min_val, max_val)
    
    return total_sum

# Main program
def main():
    n = 10000
    initial_seed = 42
    min_val = -10
    max_val = 10
    
    start_time = time.time()
    
    result = total_max_subarray_sum(n, initial_seed, min_val, max_val)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Total Maximum Subarray Sum (20 runs): {result}")
    print(f"Execution Time: {duration:.6f} seconds")

if __name__ == "__main__":
    main()""",

    "C++ Code": """#include <iostream>
#include <vector>
#include <limits>
#include <chrono>

class LCG {
private:
    uint32_t value;
    const uint32_t a = 1664525;
    const uint32_t c = 1013904223;
    const uint32_t m = 1 << 32;
    
public:
    LCG(uint32_t seed) : value(seed) {}
    
    uint32_t next() {
        value = (a * value + c) % m;
        return value;
    }
};

/*
 * Calculates maximum subarray sum for array of random numbers
 */
int64_t max_subarray_sum(int n, uint32_t seed, int min_val, int max_val) {
    LCG lcg(seed);
    std::vector<int> random_numbers(n);
    
    // Generate random numbers
    for(int i = 0; i < n; i++) {
        random_numbers[i] = (lcg.next() % (max_val - min_val + 1)) + min_val;
    }

    int64_t max_sum = std::numeric_limits<int64_t>::min();
    
    // Calculate max subarray sum
    for(int i = 0; i < n; i++) {
        int64_t current_sum = 0;
        for(int j = i; j < n; j++) {
            current_sum += random_numbers[j];
            if(current_sum > max_sum) {
                max_sum = current_sum;
            }
        }
    }
    return max_sum;
}

/*
 * Calculates total of maximum subarray sums over 20 iterations
 */
int64_t total_max_subarray_sum(int n, uint32_t initial_seed, int min_val, int max_val) {
    int64_t total_sum = 0;
    LCG lcg(initial_seed);
    
    for(int i = 0; i < 20; i++) {
        uint32_t seed = lcg.next();
        total_sum += max_subarray_sum(n, seed, min_val, max_val);
    }
    return total_sum;
}

int main() {
    const int n = 10000;
    const uint32_t initial_seed = 42;
    const int min_val = -10;
    const int max_val = 10;

    auto start_time = std::chrono::high_resolution_clock::now();
    
    int64_t result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);

    std::cout << "Total Maximum Subarray Sum (20 runs): " << result << std::endl;
    std::cout << "Execution Time: " << duration.count() / 1000000.0 << " seconds" << std::endl;

    return 0;
}""",
    "Java Code": """import java.util.ArrayList;

public class MaxSubarraySum {
    /* Linear Congruential Generator implementation */
    static class LCG {
        private long value;
        private final long a = 1664525;
        private final long c = 1013904223;
        private final long m = 1L << 32;
        
        public LCG(long seed) {
            this.value = seed;
        }
        
        public long next() {
            value = (a * value + c) % m;
            return value;
        }
    }

    /* Calculates maximum subarray sum for given array of random numbers */
    private static long maxSubarraySum(int n, long seed, int minVal, int maxVal) {
        LCG lcg = new LCG(seed);
        ArrayList<Long> randomNumbers = new ArrayList<>();
        
        // Generate random numbers
        for (int i = 0; i < n; i++) {
            long num = lcg.next() % (maxVal - minVal + 1) + minVal;
            randomNumbers.add(num);
        }

        long maxSum = Long.MIN_VALUE;
        for (int i = 0; i < n; i++) {
            long currentSum = 0;
            for (int j = i; j < n; j++) {
                currentSum += randomNumbers.get(j);
                maxSum = Math.max(maxSum, currentSum);
            }
        }
        return maxSum;
    }

    /* Calculates total of maximum subarray sums for 20 different seeds */
    private static long totalMaxSubarraySum(int n, long initialSeed, int minVal, int maxVal) {
        long totalSum = 0;
        LCG lcg = new LCG(initialSeed);
        
        for (int i = 0; i < 20; i++) {
            long seed = lcg.next();
            totalSum += maxSubarraySum(n, seed, minVal, maxVal);
        }
        return totalSum;
    }

    public static void main(String[] args) {
        // Parameters
        int n = 10000;         // Number of random numbers
        long initialSeed = 42;  // Initial seed for the LCG
        int minVal = -10;      // Minimum value of random numbers
        int maxVal = 10;       // Maximum value of random numbers

        // Timing the function
        long startTime = System.nanoTime();
        long result = totalMaxSubarraySum(n, initialSeed, minVal, maxVal);
        long endTime = System.nanoTime();

        System.out.println("Total Maximum Subarray Sum (20 runs): " + result);
        System.out.printf("Execution Time: %.6f seconds%n", (endTime - startTime) / 1e9);
    }
}"""
}

# Map snippets to their corresponding languages
SNIPPET_LANGUAGE_MAP = {
    "Python Code": "Python",
    "Python Code Simple": "Python",
    "C++ Code": "C++",
    "Java Code": "Java"
}

# CSS styling
CUSTOM_CSS = """
.code-container {
    height: 30vh;
    overflow: auto;
    border-radius: 4px;
    scrollbar-width: none;
    -ms-overflow-style: none;
}

.code-container::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    background: transparent !important;
}

.code-container .scroll-hide::-webkit-scrollbar,
.code-container > div::-webkit-scrollbar,
.code-container textarea::-webkit-scrollbar,
.code-container pre::-webkit-scrollbar,
.code-container code::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    background: transparent !important;
}

.code-container .language-select {
    overflow: auto !important;
    max-height: 100% !important;
}

.accordion {
    margin-top: 1rem !important;
}

.error-accordion {
    margin: 10px 0;
    border: 2px solid #ff4444 !important;
    border-radius: 4px !important;
    background-color: #ffffff !important;
}

.error-message {
    color: #ff4444;
    font-weight: bold;
    font-size: 16px;
    padding: 10px;
}

.gradio-container {
    padding-top: 1rem;
}

.header-text {
    text-align: center;
    font-size: 2rem;
    font-color: #283042;
    font-weight: bold;
    margin-bottom: 1rem;
}
""" 