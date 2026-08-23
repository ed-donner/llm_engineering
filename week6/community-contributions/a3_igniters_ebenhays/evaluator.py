import re
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from itertools import accumulate
import math
from tqdm.notebook import tqdm
from concurrent.futures import ThreadPoolExecutor

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
COLOR_MAP = {"red": RED, "orange": YELLOW, "green": GREEN}

WORKERS = 5
DEFAULT_SIZE = 200


class Tester:
    def __init__(
        self,
        predictor,
        data,
        title=None,
        size=DEFAULT_SIZE,
        workers=WORKERS,
        tenors=None,
    ):
        """
        Flexible evaluator that supports single-value datapoints (with .price)
        or multi-tenor datapoints (JSONL `messages` style used in the notebook).
        tenors: list of tenor keys to evaluate, e.g. ['91d','182d','364d'].
        """
        self.predictor = predictor
        self.data = data
        self.title = title or self.make_title(predictor)
        self.size = min(size, len(data))
        self.workers = workers
        # auto-detect tenors if not provided
        self.tenors = tenors or ["91d", "182d", "364d"]
        # storage per-tenor
        self.results = {
            t: {"titles": [], "guesses": [], "truths": [], "errors": [], "colors": []}
            for t in self.tenors
        }

    @staticmethod
    def make_title(predictor) -> str:
        try:
            name = predictor.__name__
        except Exception:
            name = predictor.__class__.__name__
        return name.replace("__", ".").replace("_", " ").title().replace("Gpt", "GPT")

    @staticmethod
    def post_process_value(value):
        """Parse a single numeric value from strings like '14.73%' or '$1,234' or numeric inputs."""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        # remove common clutter
        s = str(value).replace("$", "").replace(",", "").strip()
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    @staticmethod
    def parse_rates_from_text(text):
        """
        Parse assistant or predictor string for tenor rates.
        Accepts formats like:
          '91d: 14.73%, 182d: 15.16%, 364d: 18.10%'
        Returns dict {'91d': float, '182d': float, '364d': float}
        """
        if not text or not isinstance(text, str):
            return {}
        out = {}
        # find all "key: value" pairs
        pairs = re.findall(
            r"([0-9]{1,3}d|91Day|182Day|364Day|91d|182d|364d)\s*[:\-]\s*([-\d.,]+)",
            text,
            flags=re.IGNORECASE,
        )
        if not pairs:
            # fallback: find all numbers in order and map to default tenors
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", text)
            for k, n in zip(["91d", "182d", "364d"], nums):
                out[k] = float(n)
            return out
        for k, v in pairs:
            key = k.lower().replace("day", "d")
            out[key] = float(v.replace(",", ""))
        return out

    def color_for(self, error, truth):
        # relative thresholds to truth to determine color
        if truth == 0:
            return "red" if error > 1 else "green"
        if error < 0.5 or (error / truth) < 0.02:
            return "green"
        elif error < 1.5 or (error / truth) < 0.05:
            return "orange"
        else:
            return "red"

    def run_datapoint(self, i):
        datapoint = self.data[i]
        # Build a title for hover display
        title = None
        # Extract truth rates from datapoint if available
        truth_rates = {}
        # Support JSONL format with 'messages' containing assistant truth
        if isinstance(datapoint, dict) and "messages" in datapoint:
            for m in datapoint["messages"]:
                if m.get("role") == "assistant" and isinstance(m.get("content"), str):
                    truth_rates = self.parse_rates_from_text(m["content"])
                    break
            # try to make title from user message snippet
            for m in datapoint["messages"]:
                if m.get("role") == "user":
                    title = (m.get("content") or "")[:60].replace("\n", " ")
                    break
        # Support pandas row-like objects with rate columns
        elif hasattr(datapoint, "to_dict"):
            row = datapoint.to_dict()
            for k in row:
                lk = k.lower()
                if "91" in lk and "day" in lk:
                    truth_rates["91d"] = row[k]
                if "182" in lk and "day" in lk:
                    truth_rates["182d"] = row[k]
                if "364" in lk and "day" in lk:
                    truth_rates["364d"] = row[k]
            title = (
                row.get("Date", "")
                if isinstance(row.get("Date", ""), str)
                else str(row.get("Date", ""))[:60]
            )

        # Run predictor
        pred = self.predictor(datapoint)
        # Normalize predictor output to dict of rates
        pred_rates = {}
        if isinstance(pred, dict):
            # map keys to lower-case tenor keys
            for k, v in pred.items():
                lk = k.lower().replace(" ", "")
                pred_rates[lk] = self.post_process_value(v)
        elif isinstance(pred, str):
            pred_rates = self.parse_rates_from_text(pred)
        else:
            # numeric single prediction
            pred_rates = {"price": self.post_process_value(pred)}

        # For each tenor we care about, compute values if truth available
        outputs = []
        for tenor in self.tenors:
            tkey = tenor.lower()
            truth = None
            # normalize keys e.g., '91-day rate' -> '91d'
            if tkey in truth_rates:
                truth = self.post_process_value(truth_rates[tkey])
            else:
                # try variant keys
                for k in truth_rates:
                    if tkey.replace("d", "") in k:
                        truth = self.post_process_value(truth_rates[k])
                        break
            guess = pred_rates.get(tkey) or pred_rates.get(tenor) or 0.0
            guess = self.post_process_value(guess)
            error = abs(guess - (truth if truth is not None else 0.0))
            color = self.color_for(error, truth if truth is not None else guess)
            outputs.append((tenor, title or "", guess, truth, error, color))
        return outputs

    def chart_for_tenor(self, tenor, records):
        """Scatter plot truth vs guess for a single tenor."""
        df = pd.DataFrame(
            {
                "truth": [r[3] for r in records if r[3] is not None],
                "guess": [r[2] for r in records if r[3] is not None],
                "title": [r[1] for r in records if r[3] is not None],
                "error": [r[4] for r in records if r[3] is not None],
                "color": [r[5] for r in records if r[3] is not None],
            }
        )
        if df.empty:
            print(f"No truth values available for tenor {tenor}, skipping chart.")
            return
        df["hover"] = [
            f"{t}\nGuess={g:.2f}% Actual={y:.2f}%"
            for t, g, y in zip(df["title"], df["guess"], df["truth"])
        ]
        max_val = float(max(df["truth"].max(), df["guess"].max()))
        fig = px.scatter(
            df,
            x="truth",
            y="guess",
            color="color",
            color_discrete_map={"green": "green", "orange": "orange", "red": "red"},
            title=f"{self.title} — {tenor} (Truth vs Prediction)",
            labels={"truth": "Actual Rate (%)", "guess": "Predicted Rate (%)"},
            width=900,
            height=600,
        )
        for tr in fig.data:
            mask = df["color"] == tr.name
            tr.customdata = df.loc[mask, ["hover"]].to_numpy()
            tr.hovertemplate = "%{customdata[0]}<extra></extra>"
            tr.marker.update(size=6)
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

    def error_trend_for_tenor(self, tenor, records):
        errors = [r[4] for r in records if r[3] is not None]
        if not errors:
            return
        n = len(errors)
        running_sums = list(accumulate(errors))
        x = list(range(1, n + 1))
        running_means = [s / i for s, i in zip(running_sums, x)]
        running_squares = list(accumulate(e * e for e in errors))
        running_stds = [
            math.sqrt((sq_sum / i) - (mean**2)) if i > 1 else 0
            for i, sq_sum, mean in zip(x, running_squares, running_means)
        ]
        ci = [
            1.96 * (sd / math.sqrt(i)) if i > 1 else 0 for i, sd in zip(x, running_stds)
        ]
        upper = [m + c for m, c in zip(running_means, ci)]
        lower = [m - c for m, c in zip(running_means, ci)]
        fig = go.Figure()
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
        fig.add_trace(
            go.Scatter(
                x=x,
                y=running_means,
                mode="lines",
                line=dict(width=3, color="firebrick"),
                name="Cumulative Avg Error",
                customdata=list(zip(ci)),
                hovertemplate="n=%{x}<br>Avg Error=%{y:.2f}<br>±95% CI=%{customdata[0]:.2f}<extra></extra>",
            )
        )
        final_mean = running_means[-1]
        final_ci = ci[-1]
        fig.update_layout(
            title=f"{self.title} {tenor} Error: {final_mean:.2f} ± {final_ci:.2f}",
            xaxis_title="Number of Datapoints",
            yaxis_title="Average Absolute Error",
            width=900,
            height=360,
            template="plotly_white",
            showlegend=False,
        )
        fig.show()

    def report(self):
        # For each tenor compute metrics and show charts
        from statistics import mean

        for tenor in self.tenors:
            recs = []
            R = self.results.get(tenor, {})
            # build records as tuples: (tenor, title, guess, truth, error, color)
            n = len(R.get("guesses", []))
            for i in range(n):
                recs.append(
                    (
                        tenor,
                        R["titles"][i],
                        R["guesses"][i],
                        R["truths"][i],
                        R["errors"][i],
                        R["colors"][i],
                    )
                )
            if not recs:
                print(f"No data for tenor {tenor}")
                continue
            truths = [r[3] for r in recs]
            guesses = [r[2] for r in recs]
            avg_error = mean([r[4] for r in recs])
            mse = mean_squared_error(truths, guesses)
            r2 = r2_score(truths, guesses) * 100
            print(
                f"{self.title} — {tenor} — n={len(truths)} Avg Error={avg_error:.3f} MSE={mse:.3f} r2={r2:.2f}%"
            )
            self.error_trend_for_tenor(tenor, recs)
            self.chart_for_tenor(tenor, recs)

    def run(self):
        # collect per-tenor outputs then aggregate
        collected = {t: [] for t in self.tenors}
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            for outputs in tqdm(
                ex.map(self.run_datapoint, range(self.size)), total=self.size
            ):
                # outputs is a list of (tenor, title, guess, truth, error, color)
                for tenor, title, guess, truth, error, color in outputs:
                    if tenor not in collected:
                        continue
                    collected[tenor].append((tenor, title, guess, truth, error, color))
                    # store in results
                    self.results[tenor]["titles"].append(title)
                    self.results[tenor]["guesses"].append(guess)
                    self.results[tenor]["truths"].append(truth)
                    self.results[tenor]["errors"].append(error)
                    self.results[tenor]["colors"].append(color)
                    print(f"{COLOR_MAP[color]}{tenor}:{error:.2f} ", end="")
        print(RESET)
        self.report()


def evaluate(function, data, size=DEFAULT_SIZE, workers=WORKERS):
    Tester(function, data, size=size, workers=workers).run()
