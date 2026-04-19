# pscore-kmeans

K-Means clustering (K = 3) for one-dimensional pscore data, with a
reproducibility-focused workflow: a search script that finds the best random
seed against a target threshold rule, and a runner script that applies the
chosen seed to any compatible input file.

The repository contains two scripts:

| Script             | Purpose                                                              |
|--------------------|----------------------------------------------------------------------|
| `kmeans_search.py` | Sweep random seeds (0–199) and report the one that best matches the target boundaries. |
| `run_kmeans.py`    | Run K-Means with the fixed seed (`12`) on any input file and produce outputs. |

---

## Background

The dataset is a list of terms, each with a pscore in `[0, 1]`. The goal is
to partition the terms into three groups whose value ranges approximate:

```
cluster High :              value >= 1
cluster Mid  : 0.249  <=    value <  1
cluster Low  :              value <  0.249
```

Standard K-Means partitions by distance to centroids rather than by fixed
thresholds, so the assignment depends on initialization. `kmeans_search.py`
sweeps random seeds and ranks them by point-wise agreement with the target
rule; `run_kmeans.py` then applies the chosen seed deterministically.

---

## Requirements

- Python ≥ 3.9
- `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `openpyxl`

Install:

```bash
pip install pandas numpy scikit-learn matplotlib openpyxl
```

---

## Input format

A two-column Excel file (`.xlsx`), no header row required:

| column | content                |
|--------|------------------------|
| 0      | term / label (string)  |
| 1      | pscore (numeric, 0–1)  |

Rows with non-numeric or missing pscore values are dropped automatically.

---

## Usage

### 1. Find the best random seed (one-time)

```bash
python kmeans_search.py
```

The script reads a hard-coded path to the reference dataset and prints the
best seed found. With the bundled data, the result is:

```
Best random seed       : 12
Accuracy vs target rule: 98.91%
Sorted centroids       : [0.1802 0.5037 1.0000]
```

Outputs:

- `kmeans_clusters.xlsx` — original data with cluster labels
- `kmeans_clusters.png`  — 2-panel visualization

To sweep a wider range, edit the line `range(200)` in the script.

### 2. Run K-Means with the fixed seed on any file

```bash
python run_kmeans.py <input_file.xlsx> [--outdir OUTDIR]
```

Examples:

```bash
python run_kmeans.py raw-data-pscore-10Y.xlsx
python run_kmeans.py data/2024-pscore.xlsx --outdir results/
```

Outputs (written to `--outdir`, default `.`):

- `<input_basename>_clusters.xlsx`
- `<input_basename>_clusters.png`

---

## Output

### Excel file

The original two columns plus:

| column        | description                              |
|---------------|------------------------------------------|
| `cluster`     | integer label: 0 = Low, 1 = Mid, 2 = High |
| `cluster_name`| human-readable label                     |

Cluster IDs are remapped after K-Means so that 0/1/2 always correspond to
ascending centroid value, regardless of the underlying scikit-learn output.

### Visualization

Two panels:

1. **1-D jittered scatter** — every point colored by cluster, dashed lines mark the K-Means centroids, dotted lines mark the target boundaries (0.249 and 1.000).
2. **Sorted bar chart** — every point sorted by pscore and colored by its assigned cluster, with target-boundary reference lines.

---

## Reference results

Running `run_kmeans.py` on `raw-data-pscore-10Y.xlsx` (92 rows) with
`seed = 12` produces:

| cluster | range          | n  |
|---------|----------------|----|
| Low     | 0.076 – 0.310  | 8  |
| Mid     | 0.349 – 0.621  | 29 |
| High    | 1.000          | 55 |

98.91% agreement with the target rule (1 of 92 points differs: the value
`0.310` is assigned to Low rather than Mid because K-Means places the natural
boundary at the midpoint between the Low and Mid centroids, ≈ 0.34).

---

## Repository layout

```
pscore-kmeans/
├── README.md
├── kmeans_search.py          # seed-search script
├── run_kmeans.py             # fixed-seed runner
└── data/
    └── raw-data-pscore-10Y.xlsx   # example input (optional)
```

---

## Reproducibility notes

- `random_state = 12` and `n_init = 10` are fixed in both scripts. With the same scikit-learn version, results are identical across runs.
- Cluster labels are remapped by centroid order (low → mid → high), so they remain stable even if scikit-learn returns clusters in a different order across versions.
- Different input distributions may not match the target rule as closely as the reference dataset. Re-run `kmeans_search.py` if the agreement drops materially on a new dataset.

---

## License

MIT.
