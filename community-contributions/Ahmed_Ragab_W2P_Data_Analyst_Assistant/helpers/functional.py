

def print_title(title: str, n_sep: int = 70) -> None:
    title = f" {title} ".center(n_sep, "=")
    print(title, flush=True)
