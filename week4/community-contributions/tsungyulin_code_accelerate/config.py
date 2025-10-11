OPENAI_MODEL = "gpt-4o-mini"
CLAUDE_MODEL = "claude-3-5-haiku-20241022"

OUTPUT_MAX_TOKEN = 2000

PYTHON_CODE = '''
import math

def pairwise_distance(points_a, points_b):
    """
    Compute the pairwise Euclidean distance between two sets of 3D points.

    Args:
        points_a: list of (x, y, z)
        points_b: list of (x, y, z)
    Returns:
        A 2D list of shape (len(points_a), len(points_b)) representing distances
    """
    distances = []
    for i in range(len(points_a)):
        row = []
        for j in range(len(points_b)):
            dx = points_a[i][0] - points_b[j][0]
            dy = points_a[i][1] - points_b[j][1]
            dz = points_a[i][2] - points_b[j][2]
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            row.append(d)
        distances.append(row)
    return distances


# Example usage
if __name__ == "__main__":
    import random
    points_a = [(random.random(), random.random(), random.random()) for _ in range(100)]
    points_b = [(random.random(), random.random(), random.random()) for _ in range(100)]
    dists = pairwise_distance(points_a, points_b)
    print(f"Distance[0][0] = {dists[0][0]:.4f}")
'''
