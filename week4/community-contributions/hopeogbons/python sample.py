# Python Function

# This function takes a list of items and returns all possible pairs of items
def all_pairs(items):
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            pairs.append((items[i], items[j]))
    return pairs