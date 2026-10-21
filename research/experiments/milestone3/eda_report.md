# Behavioural Dataset — Exploratory Data Analysis (EDA) Report

## 1. Dataset Composition & High-Level Metrics
- **Total Daily Records:** 4,500
- **Total Variables:** 15
- **Unique Simulated Users:** 50
- **Temporal Range:** 2026-01-01 to 2026-03-31 (90 days)
- **Mean Records per User:** 90.0 (range: 90–90)
- **Duplicate User-Day Pairs:** 0 (100% unique user-date integrity)

## 2. Missingness Analysis
| Variable | Missing Count | Missing Rate (%) | Missingness Mechanism |
|---|---|---|---|
| `mood_score` | 667 | 14.82% | Simulated MCAR (Optional Self-Report) |
| `perceived_stress` | 628 | 13.96% | Simulated MCAR (Optional Self-Report) |
| `sleep_quality` | 123 | 2.73% | Simulated MCAR (Optional Self-Report) |
| `user_id` | 0 | 0.00% | Fully Observed |
| `record_date` | 0 | 0.00% | Fully Observed |
| `sleep_hours` | 0 | 0.00% | Fully Observed |
| `focus_duration_hours` | 0 | 0.00% | Fully Observed |
| `screen_time_hours` | 0 | 0.00% | Fully Observed |
| `tasks_planned` | 0 | 0.00% | Fully Observed |
| `tasks_completed` | 0 | 0.00% | Fully Observed |
| `task_difficulty_avg` | 0 | 0.00% | Fully Observed |
| `work_session_duration_hours` | 0 | 0.00% | Fully Observed |
| `inactivity_duration_hours` | 0 | 0.00% | Fully Observed |
| `interruption_count` | 0 | 0.00% | Fully Observed |
| `productivity_score` | 0 | 0.00% | Fully Observed |

## 3. Univariate Summary Statistics
| Feature | Mean | Std | Min | Median | Max | IQR | Skewness |
|---|---|---|---|---|---|---|---|
| `sleep_hours` | 7.50 | 1.01 | 4.12 | 7.50 | 11.00 | 1.39 | 0.06 |
| `sleep_quality` | 3.34 | 1.00 | 1.00 | 3.00 | 5.00 | 1.00 | -0.18 |
| `focus_duration_hours` | 4.48 | 1.46 | 0.00 | 4.50 | 9.23 | 1.96 | -0.07 |
| `screen_time_hours` | 6.68 | 1.75 | 0.00 | 6.67 | 13.42 | 2.33 | -0.05 |
| `tasks_planned` | 5.48 | 1.72 | 3.00 | 5.00 | 8.00 | 3.00 | 0.02 |
| `tasks_completed` | 2.89 | 1.57 | 0.00 | 3.00 | 8.00 | 2.00 | 0.40 |
| `task_difficulty_avg` | 3.00 | 0.87 | 1.50 | 3.00 | 4.50 | 1.51 | 0.00 |
| `work_session_duration_hours` | 5.99 | 1.55 | 0.66 | 5.99 | 11.50 | 2.07 | -0.07 |
| `inactivity_duration_hours` | 1.51 | 0.66 | 0.00 | 1.53 | 3.42 | 1.01 | -0.02 |
| `interruption_count` | 3.46 | 1.85 | 0.00 | 3.00 | 12.00 | 3.00 | 0.53 |
| `mood_score` | 2.98 | 1.41 | 1.00 | 3.00 | 5.00 | 2.00 | 0.01 |
| `perceived_stress` | 2.96 | 1.01 | 1.00 | 3.00 | 5.00 | 2.00 | 0.04 |
| `productivity_score` | 46.84 | 10.70 | 7.60 | 46.98 | 86.71 | 14.32 | -0.05 |

## 4. Bivariate & Correlation Analysis
Selected bivariate Pearson linear correlation coefficients:
- **Focus vs. Work Session Duration:** 0.927
- **Focus vs. Sleep Hours:** 0.12
- **Focus vs. Tasks Completed:** 0.301
- **Focus vs. Interruptions:** -0.101
- **Interruptions vs. Productivity Score:** -0.324

> **Methodological Limitation Notice:**
> Any correlation involving `productivity_score` reflects the generator's mathematical heuristic formula,
> not an empirical human psychological relationship. Correlations must never be interpreted as causal proof.

## 5. User Heterogeneity Analysis
| Metric | Between-User Std | Mean Within-User Std | Ratio (Between / Within) |
|---|---|---|---|
| `focus_duration_hours` | 0.797 | 1.230 | 0.647 |
| `sleep_hours` | 0.633 | 0.799 | 0.793 |
| `productivity_score` | 4.080 | 9.922 | 0.411 |
| `work_session_duration_hours` | 0.786 | 1.347 | 0.584 |

### Analytical Implication for Clustering:
- **Within-User Daily Variation:** Daily records capture short-term state fluctuations (e.g., good sleep vs. high interruptions).
- **Between-User Baseline Variation:** User-level aggregations capture distinct sustained behavioural profiles.
- **Clustering Strategy:** This justifies separating **Experiment A (Daily Pattern Clustering)** from **Experiment B (User-Level Profile Clustering)**.

## 6. Generated Visualizations
- [feature_distributions.png](results/feature_distributions.png)
- [correlation_matrix.png](results/correlation_matrix.png)
- [missingness_overview.png](results/missingness_overview.png)
- [temporal_trends.png](results/temporal_trends.png)
- [user_heterogeneity.png](results/user_heterogeneity.png)