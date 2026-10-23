# ---------------------------------
# Plot graph tool
# ---------------------------------
import os
from pathlib import Path
import math
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from helpers.system_settings import get_system_settings


def plot_graph(
    graph_type: str, 
    x         : list, 
    y         : list | None = None,
    title     : str = "", 
    x_label   : str = "", 
    y_label   : str = "",
    current_graph_index: int = 0
) -> str | dict:
    print(f'Plotting: {graph_type}')

    try:
        return _plot_graph(graph_type, x, y, title, x_label, y_label)
    except Exception as error:
        return {
            "success"   : False,
            "tool"      : "plot_graph",
            "error_type": type(error).__name__,
            "error"     : str(error),
            "hints": (
                "Use graph_type bar, line, pie, scatter, or histogram. "
                "Supply nonempty x and matching numeric y (except histogram). "
                "Line/scatter require numeric x; histogram uses numeric x only. "
                "Pie values must be nonnegative with a positive total. "
                "Correct the arguments using real query data and call plot_graph again. "
                "For filesystem errors, report the failure rather than claiming a plot was saved."
            ),
        }


def _plot_graph(
    graph_type: str, 
    x         : list, 
    y         : list | None = None,
    title     : str = "", 
    x_label   : str = "", 
    y_label   : str = "",
    current_graph_index: int = 0
) -> str:
    system_settings = get_system_settings()

    if graph_type not in {"bar", "line", "pie", "scatter", "histogram"}:
        raise ValueError("graph_type must be bar, line, pie, scatter, or histogram")
    
    if not x:
        raise ValueError("x must contain data")
    
    if graph_type != "histogram":
        if y is None or len(x) != len(y):
            raise ValueError("x and y must have the same nonzero length")
        
    numeric = x if graph_type == "histogram" else y
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in numeric):
        raise ValueError("Chart values must be finite numbers")

    if graph_type in {"line", "scatter"}:
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in x):
            raise ValueError("Line and scatter x coordinates must be finite numbers")
        
    if graph_type == "pie" and (any(v < 0 for v in y) or sum(y) <= 0):
        raise ValueError("Pie values must be nonnegative with a positive total")

    figure = Figure(figsize=(10, 6), layout="constrained")
    FigureCanvasAgg(figure)
    axis = figure.subplots()
    try:
        if graph_type == "bar":
            axis.bar([str(v) for v in x], y)
        elif graph_type == "line":
            axis.plot(x, y, marker="o")
        elif graph_type == "pie":
            axis.pie(y, labels=[str(v) for v in x], autopct="%1.1f%%")
            axis.axis("equal")
        elif graph_type == "scatter":
            axis.scatter(x, y)
        else:
            axis.hist(x, bins="auto")
        axis.set_title(title)
        if graph_type != "pie":
            axis.set_xlabel(x_label)
            axis.set_ylabel(y_label)

        output = Path(os.path.join(system_settings.PLOTS_PATH, f'plot_{current_graph_index}.png'))
        output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output, dpi=150, format="png")

    finally:
        figure.clear()
    return str(output)



