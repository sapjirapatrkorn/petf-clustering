# pscore-kmeans

K-Means clustering (K = 3) for one-dimensional pscore data, with a fixed
random seed for reproducibility. Reads a two-column Excel file, assigns each
term to one of three clusters, and writes a labeled spreadsheet plus a
visualization.

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
thresholds, so the assignment depends on initialization. The seed `12` was
selected (via an offline sweep over seeds 0–199) as the value that best
agrees with the target rule on the reference dataset, and is hard-coded in
the script for deterministic re-runs.

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

| column         | description                               |
|----------------|-------------------------------------------|
| `cluster`      | integer label: 0 = Low, 1 = Mid, 2 = High |
| `cluster_name` | human-readable label                      |

Cluster IDs are remapped after K-Means so that 0/1/2 always correspond to
ascending centroid value, regardless of the underlying scikit-learn output.

### Visualization

Two panels:

1. **1-D jittered scatter** — every point colored by cluster, dashed lines mark the K-Means centroids, dotted lines mark the target boundaries (0.249 and 1.000).
2. **Sorted bar chart** — every point sorted by pscore and colored by its assigned cluster, with target-boundary reference lines.

---

## Reference results

Running on `raw-data-pscore-10Y.xlsx` (92 rows) with `seed = 12` produces:

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
├── run_kmeans.py
└── data/
    └── raw-data-pscore-10Y.xlsx   # example input (optional)
```

---

## Reproducibility notes

- `random_state = 12` and `n_init = 10` are fixed in the script. With the same scikit-learn version, results are identical across runs.
- Cluster labels are remapped by centroid order (low → mid → high), so they remain stable even if scikit-learn returns clusters in a different order across versions.
- Different input distributions may not match the target rule as closely as the reference dataset. If agreement drops materially on a new dataset, the seed may need to be re-tuned.

---

## License

MIT.
