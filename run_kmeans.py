"""
=============================================================================
 K-Means Clustering (K=3, seed=12) for pscore data
=============================================================================

DESCRIPTION
-----------
Reads a single-column pscore dataset from an Excel file, runs K-Means with
K=3 and a fixed random seed (12), then writes:
    1) <input_basename>_clusters.xlsx  - original data + cluster labels
    2) <input_basename>_clusters.png   - 2-panel visualization

The Excel input must have two columns (no header required):
    column 0 : term / label  (string)
    column 1 : pscore        (numeric, typically 0..1)

USAGE
-----
    python run_kmeans.py <input_file.xlsx>

Examples:
    python run_kmeans.py raw-data-pscore-10Y.xlsx
    python run_kmeans.py /path/to/my_data.xlsx
    python run_kmeans.py data.xlsx --outdir results/

REQUIREMENTS
------------
    pip install pandas numpy scikit-learn matplotlib openpyxl
=============================================================================
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# -----------------------------------------------------------------------------
# Configuration (fixed)
# -----------------------------------------------------------------------------
RANDOM_SEED       = 12      # fixed seed for reproducibility
N_CLUSTERS        = 3       # K
TARGET_LOW_MID    = 0.249   # reference boundary: low  | mid
TARGET_MID_HIGH   = 1.000   # reference boundary: mid  | high


# -----------------------------------------------------------------------------
# Core functions
# -----------------------------------------------------------------------------
def load_data(input_path: Path) -> pd.DataFrame:
    """Load the Excel file and return a DataFrame with columns ['term','pscore']."""
    df = pd.read_excel(input_path, header=None, names=["term", "pscore"])
    df = df.dropna(subset=["pscore"]).reset_index(drop=True)
    df["pscore"] = pd.to_numeric(df["pscore"], errors="coerce")
    df = df.dropna(subset=["pscore"]).reset_index(drop=True)
    return df


def run_kmeans(df: pd.DataFrame, seed: int = RANDOM_SEED) -> dict:
    """Run K-Means with K=3 and remap labels so 0=low, 1=mid, 2=high."""
    X = df[["pscore"]].values
    km = KMeans(n_clusters=N_CLUSTERS, random_state=seed, n_init=10).fit(X)

    # Sort clusters by centroid value so labels are interpretable
    order = np.argsort(km.cluster_centers_.ravel())
    remap = {old: new for new, old in enumerate(order)}
    labels = np.array([remap[l] for l in km.labels_])
    centers = km.cluster_centers_.ravel()[order]

    return {"labels": labels, "centers": centers, "model": km}


def summarize(df: pd.DataFrame) -> None:
    """Print cluster sizes and value ranges."""
    name_map = {0: "Low (<0.249)",
                1: "Mid (0.249<=v<1)",
                2: "High (>=1)"}

    print("\n" + "=" * 60)
    print(f"  K-Means results (seed={RANDOM_SEED}, K={N_CLUSTERS})")
    print("=" * 60)
    for c in [0, 1, 2]:
        sub = df.loc[df["cluster"] == c, "pscore"]
        if len(sub) == 0:
            print(f"  cluster {c} ({name_map[c]:<18}): empty")
            continue
        print(f"  cluster {c} ({name_map[c]:<18}): "
              f"n={len(sub):3d}  "
              f"min={sub.min():.4f}  "
              f"max={sub.max():.4f}  "
              f"mean={sub.mean():.4f}")
    print("=" * 60 + "\n")


def plot_clusters(df: pd.DataFrame, centers: np.ndarray, output_png: Path) -> None:
    """Save a 2-panel figure: jittered scatter + sorted bar chart."""
    colors = {0: "#d62728", 1: "#ff7f0e", 2: "#2ca02c"}   # red/orange/green
    names  = {0: "Low (<0.249)", 1: "Mid (0.249<=v<1)", 2: "High (>=1)"}

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # ---- Panel A: 1-D jittered scatter -------------------------------------
    ax = axes[0]
    rng = np.random.default_rng(0)
    jitter = rng.uniform(-0.15, 0.15, size=len(df))
    for c in [0, 1, 2]:
        mask = (df["cluster"] == c).values
        if mask.any():
            ax.scatter(df.loc[mask, "pscore"], jitter[mask],
                       c=colors[c], label=f"{names[c]} (n={mask.sum()})",
                       s=55, alpha=0.75, edgecolor="black", linewidth=0.4)
    for c, val in enumerate(centers):
        ax.axvline(val, color=colors[c], ls="--", lw=1.2, alpha=0.8)
    ax.axvline(TARGET_LOW_MID,  color="black", ls=":", lw=1, alpha=0.6)
    ax.axvline(TARGET_MID_HIGH, color="black", ls=":", lw=1, alpha=0.6)
    ax.set_xlabel("pscore")
    ax.set_yticks([])
    ax.set_title(f"K-Means clusters (seed={RANDOM_SEED}, K={N_CLUSTERS})")
    ax.legend(loc="upper left", fontsize=9, frameon=True)
    ax.grid(axis="x", alpha=0.3)

    # ---- Panel B: sorted bar chart -----------------------------------------
    ax = axes[1]
    sorted_df = df.sort_values("pscore").reset_index(drop=True)
    bar_colors = [colors[c] for c in sorted_df["cluster"]]
    ax.bar(range(len(sorted_df)), sorted_df["pscore"],
           color=bar_colors, edgecolor="black", linewidth=0.3)
    ax.axhline(TARGET_LOW_MID,  color="black", ls=":", lw=1,
               label="target boundary 0.249")
    ax.axhline(TARGET_MID_HIGH, color="black", ls=":", lw=1,
               label="target boundary 1.000")
    ax.set_xlabel("term index (sorted by pscore)")
    ax.set_ylabel("pscore")
    ax.set_title("Sorted pscore values, colored by assigned cluster")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_png, dpi=140, bbox_inches="tight")
    plt.close(fig)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run K-Means (K=3, seed=12) on a pscore Excel file.")
    parser.add_argument("input_file",
                        help="Path to the input .xlsx file")
    parser.add_argument("--outdir", default=".",
                        help="Directory to write outputs (default: current dir)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_file).expanduser().resolve()
    if not input_path.is_file():
        print(f"ERROR: file not found: {input_path}", file=sys.stderr)
        return 1

    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    base = input_path.stem
    output_xlsx = outdir / f"{base}_clusters.xlsx"
    output_png  = outdir / f"{base}_clusters.png"

    print(f"Input  : {input_path}")
    print(f"Output : {output_xlsx}")
    print(f"         {output_png}")

    # 1) Load
    df = load_data(input_path)
    print(f"Loaded {len(df)} rows")

    # 2) Cluster
    result = run_kmeans(df, seed=RANDOM_SEED)
    df["cluster"] = result["labels"]
    df["cluster_name"] = df["cluster"].map({0: "Low", 1: "Mid", 2: "High"})

    # 3) Summarize
    summarize(df)
    print("Sorted centroids:", np.round(result["centers"], 4))

    # 4) Save outputs
    df.to_excel(output_xlsx, index=False)
    plot_clusters(df, result["centers"], output_png)
    print(f"\nSaved: {output_xlsx.name}")
    print(f"Saved: {output_png.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
