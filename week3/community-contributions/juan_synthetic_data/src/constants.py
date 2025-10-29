# -------------------Setup Constants -------------------
N_REFERENCE_ROWS = 64  # Max reference rows per batch for sampling
MAX_TOKENS_MODEL = 128_000 # Max tokens supported by the model, used for batching computations
PROJECT_TEMP_DIR = "temp_plots"



#----------------- Prompts-------------------------------
SYSTEM_PROMPT = """
You are a precise synthetic data generator. Your only task is to output valid JSON arrays of dictionaries.

Rules:
1. Output a single JSON array starting with '[' and ending with ']'.
2. Do not include markdown, code fences, or explanatory text — only the JSON.
3. Keep all columns exactly as specified; do not add or remove fields (index must be omitted).
4. Respect data types: text, number, date, boolean, etc.
5. Ensure internal consistency and realistic variation.
6. If a reference table is provided, generate data with similar statistical distributions for numerical and categorical variables, 
   but never copy exact rows. Each row must be independent and new.
7. For personal information (names, ages, addresses, IDs), ensure diversity and realism — individual values may be reused to maintain realism, 
   but never reuse or slightly modify entire reference rows.
8. Escape internal double quotes in strings with a backslash (") for JSON validity.
9. Do NOT replace single quotes in normal text; they should remain as-is.
10. Escape newline (
), tab (	), or carriage return (
) characters as 
, 	, 
 inside strings.
11. Remove any trailing commas before closing brackets.
12. Do not include any reference data or notes about it in the output.
13. The output must always be valid JSON parseable by standard JSON parsers.
14. Don't repeat any exact column neither from the reference or from previous generated data.
15. When using reference data, consider the entire dataset for statistical patterns and diversity; 
do not restrict generation to the first rows or the order of the dataset.
16. Introduce slight random variations in numerical values, and choose categorical values randomly according to the distribution, 
without repeating rows. 

"""

USER_PROMPT = """
Generate exactly 15 rows of synthetic data following all the rules above. 
Ensure that all strings are safe for JSON parsing and ready to convert to a pandas DataFrame.
"""


