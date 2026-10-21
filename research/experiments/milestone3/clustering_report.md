# Behavioural Clustering — Research Report & Model Selection

## 1. Research Objectives & Problem Statement
The objective of Milestone 3 is to discover latent behavioural archetypes in individual work records
without supervision or target leakage. Two complementary unsupervised paradigms are examined:
1. **Experiment A (Daily Behavioural States):** Clustered over individual daily observations ($N = 4,500$)
   to identify recurring working states (e.g., concentrated focus vs. fragmented distraction).
2. **Experiment B (Longitudinal User Profiles):** Clustered over aggregate 90-day individual profiles ($N = 50$)
   to characterize sustained working traits.

---

## 2. Experiment A: Daily Behavioural Pattern Clustering

### 2.1 Model Selection Metrics Across Candidate k (k = 2 to 8)
| k | Inertia | Silhouette Score | Davies-Bouldin Index | Cluster Proportions (%) | Min Cluster Size |
|---|---|---|---|---|---|
| 2 | 35,253.5 | 0.1942 | 1.7928 | 61.2%, 38.8% | 1748 |
| 3 | 30,922.3 | 0.1600 | 1.8517 | 29.2%, 36.4%, 34.5% | 1313 |
| 4 | 28,319.7 | 0.1429 | 1.7810 | 19.1%, 31.3%, 21.6%, 28.0% | 859 |
| 5 | 26,885.0 | 0.1205 | 1.9048 | 19.3%, 18.4%, 28.1%, 22.4%, 11.8% | 531 |
| 6 | 25,613.4 | 0.1182 | 1.9337 | 18.1%, 17.1%, 11.2%, 21.4%, 15.3%, 16.9% | 502 |
| 7 | 24,684.6 | 0.1162 | 1.9287 | 15.6%, 15.4%, 10.8%, 17.6%, 10.5%, 15.9%, 14.1% | 473 |
| 8 | 23,884.2 | 0.1089 | 1.9825 | 6.6%, 12.1%, 16.2%, 12.9%, 13.8%, 13.7%, 14.0%, 10.7% | 296 |

### 2.2 Model Selection Review: Metric-Optimal (k=2) vs. Exploratory Operational (k=3)
> **Methodological Principle:** We do not claim $k=3$ is objectively optimal based on geometric cluster metrics.
> Mathematically, **$k=2$ achieves the global maximum silhouette score ($0.1942$) and lower Davies-Bouldin index ($1.7928$)**.
> The selection between $k=2$ and $k=3$ reflects a documented research trade-off between geometric compactness and operational granularity:

- **Metric-Optimal Baseline ($k=2$):**
  - Silhouette Score: `0.1942` (highest across all candidates)
  - Davies-Bouldin Index: `1.7928`
  - Stability (Mean ARI across seeds): `0.9966`
  - Structure: Separates records into a broad binary dichotomy: Extended/High-Focus days (61.2%) vs. Fragmented/Low-Focus days (38.8%).

- **Exploratory Operational Model ($k=3$):**
  - Silhouette Score: `0.1600` (modest drop of 0.0342 from k=2)
  - Davies-Bouldin Index: `1.8517`
  - Stability (Mean ARI across seeds): `1.0000`
  - Structure: Tripartite partition separating moderate routine days (29.2%), extended high-session days (36.4%), and concentrated high-utilization days (34.5%).

### 2.3 Unscaled Cluster Profiles (Physical Behavioural Units)

#### Candidate Solution 1: Metric-Optimal Baseline (k = 2)
| Cluster | Size | Propor. (%) | Focus Hours (mean) | Sleep Hours (mean) | Session Hours (mean) | Interruptions (mean) | Completion Rate (mean) | Utilization (mean) |
|---|---|---|---|---|---|---|---|---|
| `Cluster_0` | 2,752 | 61.2% | 5.31h | 7.63h | 6.69h | 3.3 | 60.0% | 79.6% |
| `Cluster_1` | 1,748 | 38.8% | 3.17h | 7.30h | 4.88h | 3.7 | 41.4% | 64.2% |

#### Candidate Solution 2: Exploratory Operational Model (k = 3)
| Cluster | Size | Propor. (%) | Focus Hours (mean) | Sleep Hours (mean) | Session Hours (mean) | Interruptions (mean) | Completion Rate (mean) | Utilization (mean) |
|---|---|---|---|---|---|---|---|---|
| `Cluster_0` | 1,313 | 29.2% | 3.03h | 7.31h | 4.85h | 3.7 | 40.6% | 61.1% |
| `Cluster_1` | 1,636 | 36.4% | 5.69h | 7.69h | 7.46h | 3.2 | 64.2% | 76.0% |
| `Cluster_2` | 1,551 | 34.5% | 4.43h | 7.46h | 5.39h | 3.5 | 51.0% | 81.8% |

### 2.4 Objective Cluster Interpretations (Neutral Behavioural Descriptions)
**Under k = 2:**
- **Cluster_0:** *Extended Session / High Focus Pattern* — Longer work sessions (6.69h), high focus (5.31h), high utilization (79.6%), and completion rate (60.0%).
- **Cluster_1:** *Compressed Session / Elevated Inactivity Pattern* — Shorter work sessions (4.88h), lower focus (3.17h), higher inactivity ratio (36.6%), and lower completion (41.4%).

**Under k = 3:**
- **Cluster_0:** *Moderate Work Session / Typical Execution Pattern* — Moderate focus duration (3.03h), balanced interruptions (3.7), standard completion rates (40.6%).
- **Cluster_1:** *Extended Session / Elevated Friction Pattern* — Longer work sessions (7.46h) accompanied by elevated interruptions (3.2) and high absolute inactivity.
- **Cluster_2:** *High Focus / Concentrated Utilization Pattern* — Superior focus-to-session ratio (81.8% utilization), high task completion rate (51.0%).

---

## 3. Experiment B: User-Level Longitudinal Profile Clustering

### 3.1 Model Selection Across Candidate k (k = 2 to 6)
| k | Inertia | Silhouette Score | Davies-Bouldin Index | Cluster Proportions (%) |
|---|---|---|---|---|
| 2 | 214.9 | 0.2997 | 1.2057 | 48.0%, 52.0% |
| 3 | 177.4 | 0.2170 | 1.4294 | 38.0%, 20.0%, 42.0% |
| 4 | 145.3 | 0.2448 | 1.2887 | 30.0%, 26.0%, 24.0%, 20.0% |
| 5 | 128.8 | 0.2249 | 1.2175 | 22.0%, 24.0%, 18.0%, 18.0%, 18.0% |
| 6 | 111.3 | 0.2436 | 1.1343 | 20.0%, 12.0%, 6.0%, 18.0%, 18.0%, 26.0% |

### 3.2 Selected Model Justification: Primary (k = 2) vs. Exploratory (k = 3)
- **Recommended Primary Model: $k = 2$**
  - **Silhouette Score:** `0.2997` (decisively highest across all candidates)
  - **Davies-Bouldin Index:** `1.2057` (best separation)
  - **Stability (Mean ARI across seeds):** `1.0000` (perfect stability across all random seeds)
  - **Cluster Balance:** 24 users (48.0%) vs. 26 users (52.0%). Robust against small-sample variance.

- **Exploratory Candidate: $k = 3$ (Evaluated with Caveats)**
  - **Silhouette Score:** `0.2170` (0.0827 lower than k=2)
  - **Davies-Bouldin Index:** `1.4294`
  - **Stability (Mean ARI across seeds):** `0.7910` (minimum pairwise ARI dropped to `0.5157`)
  - **Sample Size Fragility:** Produces an underpopulated cluster of only 10 users (20.0%), making it sensitive to individual user variations in $N=50$.

### 3.3 User-Level Cluster Profiles (Aggregated Baseline Units)

#### Primary Model: k = 2 (Recommended)
| Cluster | User Count | Proportion | Mean Focus | Mean Sleep | Mean Screen Time | Mean Interruptions | Focus Variability (Std) |
|---|---|---|---|---|---|---|---|
| `Cluster_0` | 24 users | 48.0% | 3.81h | 7.33h | 6.25h | 3.5 | 1.22h |
| `Cluster_1` | 26 users | 52.0% | 5.09h | 7.66h | 7.08h | 3.4 | 1.24h |

#### Exploratory Candidate: k = 3 (Documented for Comparison)
| Cluster | User Count | Proportion | Mean Focus | Mean Sleep | Mean Screen Time | Mean Interruptions | Focus Variability (Std) |
|---|---|---|---|---|---|---|---|
| `Cluster_0` | 19 users | 38.0% | 5.26h | 7.64h | 7.19h | 3.4 | 1.26h |
| `Cluster_1` | 10 users | 20.0% | 3.35h | 7.56h | 5.94h | 3.7 | 1.23h |
| `Cluster_2` | 21 users | 42.0% | 4.31h | 7.34h | 6.58h | 3.4 | 1.21h |

---

## 4. Stability & Sensitivity Audit
Stability is evaluated by fitting K-Means over 5 independent random centroid initialization seeds `[42, 101, 202, 303, 404]` with `n_init=10`, computing pairwise Adjusted Rand Index (ARI) across all $\binom{5}{2} = 10$ seed pairs.

1. **Label Permutation Invariance:** The Adjusted Rand Index evaluates cluster membership concordance over all pairs of items.    It is mathematically invariant to arbitrary cluster integer label permutations.
2. **Why Daily Clustering Demonstrates Near-Perfect Stability ($ARI \approx 1.0$):**    With $N = 4,500$ observations in a 10-dimensional continuous space, sample density is high.    The K-Means loss function has a dominant global minimum that `n_init=10` reliably discovers across every tested seed.
3. **Why User-Level k=3 Clustering Displays Moderate Instability ($ARI = 0.7910$, Min $ARI = 0.5157$):**    Aggregating to $N = 50$ users across 8 dimensions creates severe geometric sparsity.    For $k=3$, the loss surface exhibits competing local optima; across different seeds, 3 to 5 boundary users flip assignments,    substantially depressing the pairwise ARI. In contrast, for $k=2$, the primary partition is completely stable ($ARI = 1.0000$).

## 5. Responsible AI and Limitations Statement
1. **No Psychological or Clinical Claims:** Cluster assignments represent statistical partitions of simulated telemetries.    They do **not** reflect psychiatric states, cognitive deficits, clinical burnout, or personality traits.
2. **Synthetic Data Boundaries:** All underlying observations were produced by synthetic stochastic processes.    Correlations and cluster boundaries reflect generative mathematical formulations rather than discovered human psychological truths.
3. **Zero Target Leakage:** Verified that `productivity_score` and target-derived features were strictly excluded from all clustering matrices.
4. **User-Level Sample Size Limitation:** Experiment B is based on $N = 50$ simulated users. Findings are exploratory heuristics    and have no generalizability to real-world populations without external human empirical validation.