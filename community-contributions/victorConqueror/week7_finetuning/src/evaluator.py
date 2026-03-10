"""Evaluation and visualization tools"""

import re
import math
from itertools import accumulate
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import mean_squared_error, r2_score
from tqdm.notebook import tqdm

# Terminal colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
COLOR_MAP = {"red": RED, "orange": YELLOW, "green": GREEN}

DEFAULT_SIZE = 200
WORKERS = 5


class Tester:
    """
    Comprehensive testing and evaluation framework
    Tests a predictor function on a dataset and generates visualizations
    """

    def __init__(
        self,
        predictor: Callable,
        data: List,
        title: str = None,
        size: int = DEFAULT_SIZE,
        workers: int = WORKERS
    ):
        """
        Args:
            predictor: Function that takes an Item and returns a price prediction
            data: List of Items to test on
            title: Display title for charts
            size: Number of items to test
            workers: Number of parallel workers
        """
        self.predictor = predictor
        self.data = data[:size]
        self.title = title or self.make_title(predictor)
        self.size = min(size, len(data))
        self.workers = workers
        
        # Results storage
        self.titles = []
        self.guesses = []
        self.truths = []
        self.errors = []
        self.colors = []

    @staticmethod
    def make_title(predictor) -> str:
        """Generate title from function name"""
        return (
            predictor.__name__
            .replace("__", ".")
            .replace("_", " ")
            .title()
            .replace("Gpt", "GPT")
        )

    @staticmethod
    def post_process(value) -> float:
        """Extract numeric price from string or return float"""
        if isinstance(value, str):
            value = value.replace("$", "").replace(",", "")
            match = re.search(r"[-+]?\d*\.\d+|\d+", value)
            return float(match.group()) if match else 0.0
        return float(value)

    def color_for(self, error: float, truth: float) -> str:
        """Determine color based on error magnitude"""
        if error < 40 or error / truth < 0.2:
            return "green"
        elif error < 80 or error / truth < 0.4:
            return "orange"
        else:
            return "red"

    def run_datapoint(self, i: int) -> tuple:
        """Test a single datapoint"""
        datapoint = self.data[i]
        
        # Get prediction
        value = self.predictor(datapoint)
        guess = self.post_process(value)
        truth = datapoint.price
        error = abs(guess - truth)
        color = self.color_for(error, truth)
        
        # Format title
        title = datapoint.title
        if len(title) > 40:
            title = title[:40] + "..."
        
        return title, guess, truth, error, color

    def chart(self, title: str):
        """Generate scatter plot of predictions vs actual prices"""
        df = pd.DataFrame({
            "truth": self.truths,
            "guess": self.guesses,
            "title": self.titles,
            "error": self.errors,
            "color": self.colors,
        })

        # Pre-format hover text
        df["hover"] = [
            f"{t}\nGuess=${g:,.2f} Actual=${y:,.2f}"
            for t, g, y in zip(df["title"], df["guess"], df["truth"])
        ]

        max_val = float(max(df["truth"].max(), df["guess"].max()))

        fig = px.scatter(
            df,
            x="truth",
            y="guess",
            color="color",
            color_discrete_map={"green": "green", "orange": "orange", "red": "red"},
            title=title,
            labels={"truth": "Actual Price", "guess": "Predicted Price"},
            width=1000,
            height=800,
        )

        # Assign customdata per trace
        for tr in fig.data:
            mask = df["color"] == tr.name
            tr.customdata = df.loc[mask, ["hover"]].to_numpy()
            tr.hovertemplate = "%{customdata[0]}<extra></extra>"
            tr.marker.update(size=6)

        # Reference line y=x
        fig.add_trace(
            go.Scatter(
                x=[0, max_val],
                y=[0, max_val],
                mode="lines",
                line=dict(width=2, dash="dash", color="deepskyblue"),
                name="y = x",
                hoverinfo="skip",
                showlegend=False,
            )
        )

        fig.update_xaxes(range=[0, max_val])
        fig.update_yaxes(range=[0, max_val])
        fig.update_layout(showlegend=False)
        fig.show()

    def error_trend_chart(self):
        """Generate running average error chart with confidence intervals"""
        n = len(self.errors)

        # Running mean and std
        running_sums = list(accumulate(self.errors))
        x = list(range(1, n + 1))
        running_means = [s / i for s, i in zip(running_sums, x)]

        running_squares = list(accumulate(e * e for e in self.errors))
        running_stds = [
            math.sqrt((sq_sum / i) - (mean**2)) if i > 1 else 0
            for i, sq_sum, mean in zip(x, running_squares, running_means)
        ]

        # 95% confidence interval
        ci = [
            1.96 * (sd / math.sqrt(i)) if i > 1 else 0 
            for i, sd in zip(x, running_stds)
        ]
        upper = [m + c for m, c in zip(running_means, ci)]
        lower = [m - c for m, c in zip(running_means, ci)]

        # Plot
        fig = go.Figure()

        # Shaded confidence interval
        fig.add_trace(
            go.Scatter(
                x=x + x[::-1],
                y=upper + lower[::-1],
                fill="toself",
                fillcolor="rgba(128,128,128,0.2)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=False,
                name="95% CI",
            )
        )

        # Main line
        fig.add_trace(
            go.Scatter(
                x=x,
                y=running_means,
                mode="lines",
                line=dict(width=3, color="firebrick"),
                name="Cumulative Avg Error",
                customdata=list(zip(ci)),
                hovertemplate=(
                    "n=%{x}<br>"
                    "Avg Error=$%{y:,.2f}<br>"
                    "±95% CI=$%{customdata[0]:,.2f}<extra></extra>"
                ),
            )
        )

        # Title with final stats
        final_mean = running_means[-1]
        final_ci = ci[-1]
        title = f"{self.title} Error: ${final_mean:,.2f} ± ${final_ci:,.2f}"

        fig.update_layout(
            title=title,
            xaxis_title="Number of Datapoints",
            yaxis_title="Average Absolute Error ($)",
            width=1000,
            height=360,
            template="plotly_white",
            showlegend=False,
        )

        fig.show()

    def report(self):
        """Generate comprehensive evaluation report"""
        average_error = sum(self.errors) / self.size
        mse = mean_squared_error(self.truths, self.guesses)
        r2 = r2_score(self.truths, self.guesses) * 100
        
        title = (
            f"{self.title} results<br>"
            f"<b>Error:</b> ${average_error:,.2f} "
            f"<b>MSE:</b> {mse:,.0f} "
            f"<b>r²:</b> {r2:.1f}%"
        )
        
        self.error_trend_chart()
        self.chart(title)
        
        return {
            "average_error": average_error,
            "mse": mse,
            "r2": r2
        }

    def run(self):
        """Run evaluation with progress bar"""
        print(f"Testing {self.title} on {self.size} items...")
        
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            for title, guess, truth, error, color in tqdm(
                ex.map(self.run_datapoint, range(self.size)), 
                total=self.size
            ):
                self.titles.append(title)
                self.guesses.append(guess)
                self.truths.append(truth)
                self.errors.append(error)
                self.colors.append(color)
                print(f"{COLOR_MAP[color]}${error:.0f} ", end="")
        
        print(f"\n{RESET}")
        return self.report()


def evaluate(
    function: Callable,
    data: List,
    size: int = DEFAULT_SIZE,
    workers: int = WORKERS
) -> dict:
    """
    Convenience function to evaluate a predictor
    
    Args:
        function: Predictor function
        data: Test data
        size: Number of samples to test
        workers: Number of parallel workers
    
    Returns:
        Dictionary with metrics
    """
    tester = Tester(function, data, size=size, workers=workers)
    return tester.run()
