import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional
from PIL import Image
import pandas as pd
import os

class SimpleEvaluator:
    """
    Evaluates synthetic data against a reference dataset, providing summary statistics and visualizations.
    """

    def __init__(self, temp_dir: str = "temp_plots"):
        """
        Initialize the evaluator.

        Args:
            temp_dir (str): Directory to save temporary plot images.
        """
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)

    def evaluate(self, reference_df: pd.DataFrame, generated_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compare numerical and categorical columns between reference and generated datasets.
        """
        self.results: Dict[str, Any] = {}
        self.common_cols = list(set(reference_df.columns) & set(generated_df.columns))

        for col in self.common_cols:
            if pd.api.types.is_numeric_dtype(reference_df[col]):
                self.results[col] = {
                    "type": "numerical",
                    "ref_mean": reference_df[col].mean(),
                    "gen_mean": generated_df[col].mean(),
                    "mean_diff": generated_df[col].mean() - reference_df[col].mean(),
                    "ref_std": reference_df[col].std(),
                    "gen_std": generated_df[col].std(),
                    "std_diff": generated_df[col].std() - reference_df[col].std(),
                }
            else:
                ref_counts = reference_df[col].value_counts(normalize=True)
                gen_counts = generated_df[col].value_counts(normalize=True)
                overlap = sum(min(ref_counts.get(k, 0), gen_counts.get(k, 0)) for k in ref_counts.index)
                self.results[col] = {
                    "type": "categorical",
                    "distribution_overlap_pct": round(overlap * 100, 2),
                    "ref_unique": len(ref_counts),
                    "gen_unique": len(gen_counts)
                }

        return self.results

    def results_as_dataframe(self) -> pd.DataFrame:
        """
        Convert the evaluation results into a pandas DataFrame for display.
        """
        rows = []
        for col, stats in self.results.items():
            if stats["type"] == "numerical":
                rows.append({
                    "Column": col,
                    "Type": "Numerical",
                    "Ref Mean/Std": f"{stats['ref_mean']:.2f} / {stats['ref_std']:.2f}",
                    "Gen Mean/Std": f"{stats['gen_mean']:.2f} / {stats['gen_std']:.2f}",
                    "Diff": f"Mean diff: {stats['mean_diff']:.2f}, Std diff: {stats['std_diff']:.2f}"
                })
            else:
                rows.append({
                    "Column": col,
                    "Type": "Categorical",
                    "Ref": f"{stats['ref_unique']} unique",
                    "Gen": f"{stats['gen_unique']} unique",
                    "Diff": f"Overlap: {stats['distribution_overlap_pct']}%"
                })
        return pd.DataFrame(rows)

    def create_visualizations_temp_dict(
        self,
        reference_df: pd.DataFrame,
        generated_df: pd.DataFrame,
        percentage: bool = True
    ) -> Dict[str, List[Optional[Image.Image]]]:
        """
        Create histogram and boxplot visualizations for each column and save them as temporary images.
        Handles special characters in column names and category labels.
        """
        vis_dict: Dict[str, List[Optional[Image.Image]]] = {}
        common_cols = list(set(reference_df.columns) & set(generated_df.columns))

        for col in common_cols:
            col_safe = str(col).replace("_", r"\_").replace("$", r"\$")  # Escape special chars

            # ---------------- Histogram ----------------
            plt.figure(figsize=(6, 4))
            if pd.api.types.is_numeric_dtype(reference_df[col]):
                sns.histplot(reference_df[col], color="blue", label="Reference",
                            stat="percent" if percentage else "count", alpha=0.5)
                sns.histplot(generated_df[col], color="orange", label="Generated",
                            stat="percent" if percentage else "count", alpha=0.5)
            else:  # Categorical
                ref_counts = reference_df[col].value_counts(normalize=percentage)
                gen_counts = generated_df[col].value_counts(normalize=percentage)
                categories = list(set(ref_counts.index) | set(gen_counts.index))
                categories_safe = [str(cat).replace("_", r"\_").replace("$", r"\$") for cat in categories]
                ref_vals = [ref_counts.get(cat, 0) for cat in categories]
                gen_vals = [gen_counts.get(cat, 0) for cat in categories]

                x = range(len(categories))
                width = 0.4
                plt.bar([i - width/2 for i in x], ref_vals, width=width, color="blue", alpha=0.7, label="Reference")
                plt.bar([i + width/2 for i in x], gen_vals, width=width, color="orange", alpha=0.7, label="Generated")
                plt.xticks(x, categories_safe, rotation=45, ha="right")

            plt.title(f"Histogram comparison for '{col_safe}'", fontsize=12, usetex=False)
            plt.legend()
            plt.tight_layout()
            hist_path = os.path.join(self.temp_dir, f"{col}_hist.png")
            plt.savefig(hist_path, bbox_inches='tight')
            plt.close()
            hist_img = Image.open(hist_path)

            # ---------------- Boxplot (numerical only) ----------------
            box_img = None
            if pd.api.types.is_numeric_dtype(reference_df[col]):
                plt.figure(figsize=(6, 4))
                df_box = pd.DataFrame({
                    'Value': pd.concat([reference_df[col], generated_df[col]], ignore_index=True),
                    'Dataset': ['Reference']*len(reference_df[col]) + ['Generated']*len(generated_df[col])
                })

                sns.boxplot(x='Dataset', y='Value', data=df_box, palette=['#1f77b4','#ff7f0e'])
                plt.title(f"Boxplot comparison for '{col_safe}'", fontsize=12, usetex=False)
                plt.tight_layout()
                box_path = os.path.join(self.temp_dir, f"{col}_box.png")
                plt.savefig(box_path, bbox_inches='tight')
                plt.close()
                box_img = Image.open(box_path)

            vis_dict[col] = [hist_img, box_img]

        return vis_dict
