import sys, modal

app = modal.App("example-hello-world")

@app.function()
def f(i: int) -> int:
    if i % 2 == 0:
        print("hello", i)
    else:
        print("world", i, file=sys.stderr)

    return i * i
