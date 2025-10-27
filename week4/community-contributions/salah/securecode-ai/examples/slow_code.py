"""Example inefficient code for testing performance analysis."""

# Example 1: O(n²) complexity - inefficient duplicate finder
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates


# Example 2: Inefficient string concatenation
def build_large_string(items):
    result = ""
    for item in items:
        result += str(item) + ","
    return result


# Example 3: Unnecessary repeated calculations
def calculate_totals(orders):
    totals = []
    for order in orders:
        total = 0
        for item in order["items"]:
            # Recalculating tax each time
            tax_rate = 0.08
            total += item["price"] * (1 + tax_rate)
        totals.append(total)
    return totals


# Example 4: Loading all data into memory
def process_large_file(filename):
    with open(filename, "r") as f:
        all_lines = f.readlines()  # Loads entire file into memory

    processed = []
    for line in all_lines:
        if "ERROR" in line:
            processed.append(line.strip())
    return processed


# Example 5: N+1 query problem simulation
def get_user_posts(user_ids):
    posts = []
    for user_id in user_ids:
        # Simulates making a separate database query for each user
        user_posts = fetch_posts_for_user(user_id)  # N queries
        posts.extend(user_posts)
    return posts


def fetch_posts_for_user(user_id):
    # Simulate database query
    return [f"Post from user {user_id}"]
