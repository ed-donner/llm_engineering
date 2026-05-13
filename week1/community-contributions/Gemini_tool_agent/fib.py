def fib(n: int) -> int:
    """Calculates the Nth Fibonacci number efficiently."""
    print(f"DEBUG: Gemini calling fib(n={n})")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def printout():
    return "YEs its executed"



import requests

def call_api():

    url = "https://www.thunderclient.com/welcome"
    
    try:
        response = requests.get(url,timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"Error calling API: {e}"