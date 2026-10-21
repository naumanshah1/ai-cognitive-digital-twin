# Regression-Based Productivity Prediction — Research Report

## 1. Research Objectives, Problem Formulation, & Temporal Framing
The objective of Milestone 4 is to develop, rigorously evaluate, and interpret supervised regression models
that predict individual daily productivity (`productivity_score` $\in [0, 100]$) from strictly permissible
behavioural telemetries without target leakage or future-information corruption.

### Operational Temporal Framing (Retrospective Daily Assessment):
- **Estimation Mode:** The task is formulated as **end-of-day retrospective productivity estimation / daily diagnostic assessment**.
  At the close of day $t$, daily telemetry logs (such as night sleep hours, daytime focus duration, interruptions, and task difficulty)
  are finalized, and the model estimates the unobserved cognitive productivity score for that completed day.
- **Forecasting Distinction:** This task differs fundamentally from pre-day prognostic forecasting (predicting tomorrow's productivity
  before daytime activities occur). Future prognostic sequence modeling using strictly historical lags ($t-1, t-2, \dots$)
  is scheduled for subsequent milestones.

### Key Methodological Safeguards:
1. **Strict Target Leakage Exclusion:** `productivity_score` and target-derived rolling aggregates (`rolling_productivity_mean_7d`, `productivity_change_7d`) are completely forbidden from predictor matrices.
2. **Strict Chronological Splitting:** Observations are partitioned chronologically along date boundaries (Train: 70%, Validation: 15%, Test: 15%) to evaluate temporal generalization rather than random interpolation.
3. **Train-Only Preprocessing:** Imputation medians, IQR outlier clipping bounds, and `StandardScaler` parameters are fitted strictly on the training partition and frozen before applying to validation and test sets.
4. **Separation of Model Selection and Test Evaluation:** Model selection is conducted exclusively on validation data. The test partition is evaluated exactly once on the chosen champion model.
5. **Causal Rolling History:** All rolling temporal aggregates (such as `rolling_focus_std_7d`) strictly apply a one-day shift (`shift(1)`) prior to window calculation, ensuring no same-day telemetry enters historical summary windows.

---

## 2. Dataset, Splits, and Target Audit

### 2.1 Ground-Truth Generative Heuristic & Noise Floor Audit
The synthetic target `productivity_score` was generated via the following programmed heuristic:
```text
latent_score = 30.0 + 4.0 * focus + 3.0 * (sleep - 7.0) + 3.0 * user_consistency \
               - 1.5 * interruptions - 2.0 * (task_difficulty - 3.0) + N(0, 7.0)
productivity_score = clip(latent_score, 0.0, 100.0)
```

#### Critical Audit of Theoretical vs. Empirical Error Floor:
1. **Latent Additive Noise ($\\sigma = 7.0$):** The stochastic component $\\mathcal{N}(0, \\sigma=7.0)$ represents the asymptotic
   standard deviation of irreducible Gaussian noise in the unclipped linear regime.
2. **Clipping Boundary Analysis:** The function applies bounds $[0.0, 100.0]$. Truncation or censoring can alter variance
   (and even compress tail error below $\sigma$). However, an audit of the generated 4,500 records confirms that
   observed `productivity_score` values strictly span $[7.60, 86.71]$. Because no observation reached $0.0$ or $100.0$,
   **clipping remained entirely inactive** in this dataset realization.
3. **Unobserved Latent Variable Variance:** The generator includes a user-level latent term $3.0 \times \text{user\_consistency}$,
   where $\text{user\_consistency} \sim \text{Uniform}(0.75, 1.0)$. Because user identity is excluded from predictors to
   prevent overfitting, this introduces minor unobserved user intercept variance ($\sigma_u \approx 0.22$ points).
4. **Finite-Sample Realization on Test Partition ($N=700$):** On the finite test set of 700 observations, the empirical sample
   standard deviation of the realized Gaussian noise draws is $s = 6.962$ and the empirical noise root-mean-square is **6.957** points.
5. **Oracle Model Benchmark:** A theoretical Oracle predictor (possessing exact knowledge of all generative slopes and mean consistency)
   evaluated on the test partition achieves **RMSE = 6.956** ($R^2 = 0.5872$).
6. **Conclusion:** Describing $\text{RMSE} = 7.0$ as a universal mathematical lower bound for arbitrary clipped targets is mathematically unproven;
   rather, $\sigma = 7.0$ is the asymptotic standard deviation of the additive stochastic component. The observed Test RMSE of **6.965**
   from our Linear Regression champion approaches within $0.009$ points of the empirical Oracle benchmark.

### 2.2 Chronological Partition Boundaries
| Partition | Sample Size (N) | Date Range | Calendar Days | User Count |
|---|---|---|---|---|
| **Training (70%)** | 3,150 | `2026-01-01` to `2026-03-04` | 63 | 50 |
| **Validation (15%)** | 650 | `2026-03-05` to `2026-03-17` | 13 | 50 |
| **Test (15%)** | 700 | `2026-03-18` to `2026-03-31` | 14 | 50 |

### 2.3 Permitted Predictor Feature Matrix (19 Features)
`sleep_hours`, `sleep_quality`, `focus_duration_hours`, `screen_time_hours`, `tasks_planned`, `tasks_completed`, `task_difficulty_avg`, `work_session_duration_hours`, `inactivity_duration_hours`, `interruption_count`, `mood_score`, `perceived_stress`, `task_completion_rate`, `work_session_utilization`, `inactivity_ratio`, `day_of_week`, `is_weekend`, `rolling_focus_std_7d`, `work_session_frequency_7d`

---

## 3. Model Evaluation and Selection

### 3.1 Candidate Model Performance Comparison
| Candidate Model | Train MAE | Train RMSE | Train $R^2$ | Val MAE | Val RMSE | Val $R^2$ |
|---|---|---|---|---|---|---|
| **Dummy (Mean Baseline)** | 8.370 | 10.569 | 0.0000 | 8.998 | 11.183 | -0.0058 |
| **Linear Regression** | 5.556 | 6.983 | 0.5634 | 5.869 | 7.369 | 0.5633 |
| **Ridge Regression (L2)** | 5.556 | 6.983 | 0.5634 | 5.869 | 7.369 | 0.5633 |
| **Random Forest Regressor** | 4.430 | 5.513 | 0.7279 | 6.097 | 7.667 | 0.5272 |
| **Gradient Boosting Regressor** | 5.302 | 6.636 | 0.6058 | 6.091 | 7.607 | 0.5346 |

### 3.2 Methodological Baselines and Persistence Analysis
- **Dummy Regressor (Mean Baseline):** Predicts the training set target mean ($47.05$ points) for all records. On the validation set, it achieves MAE = 8.998, RMSE = 11.183, and $R^2 = -0.0058$. Out-of-sample $R^2$ is slightly negative because the training mean slightly deviates from the validation sample mean.
- **Lag-1 Persistence Baseline ($\hat{y}_{u, t} = y_{u, t-1}$):** Predicts each user's previous observed target. On the validation set ($N=650$), it achieves MAE = 11.721, RMSE = 14.687, and $R^2 = -0.7349$. On the test set ($N=700$), it achieves MAE = 10.994, RMSE = 13.799, and $R^2 = -0.6244$.
- **Causal Split Boundary Handling:** For the first validation date (`2026-03-05`), each user's prediction strictly draws from their observed target on `2026-03-04` (the final day of the training set). Similarly, the first test date (`2026-03-18`) draws from `2026-03-17` (the final day of the validation set). No future information or cross-partition leakage is introduced.
- **Explanation of Negative $R^2$ on Persistence:** Out-of-sample $R^2 = 1 - \frac{\sum (y_t - y_{t-1})^2}{\sum (y_t - \bar{y})^2}$. Because daily cognitive productivity is governed by same-day behavioural fluctuations (focus, sleep, interruptions) rather than an integrated random walk, $y_t$ and $y_{t-1}$ are weakly auto-correlated. When $y_t = \mu + \epsilon_t$ with i.i.d. noise, $\mathbb{E}[(y_t - y_{t-1})^2] \approx 2 \text{Var}(y)$, resulting in theoretical $R^2 \approx 1 - 2 = -1.0$. This confirms that yesterday's target alone is insufficient for productivity tracking, demonstrating the substantial diagnostic value added by contemporaneous behavioral telemetries.

### 3.3 Model Selection Rationale
- **Selected Champion Model:** **Linear Regression**
- **Selection Criterion:** Validation RMSE minimization (`val_rmse` = `7.3686`).
- **Overfitting Analysis:**
  - Linear Regression displays virtually zero overfitting: Train $R^2 = 0.5634$ vs. Validation $R^2 = 0.5633$.
  - In contrast, Random Forest exhibited training overfitting (Train $R^2 \approx 0.73$ vs. Val $R^2 \approx 0.53$), as decision trees partition continuous linear features into axis-aligned step functions and fit to training noise.
  - Because the underlying synthetic target mechanism is predominantly linear with additive noise, Linear Regression achieves the lowest validation RMSE and highest validation $R^2$ while remaining parsimonious and fully interpretable.

---

## 4. Final Test Set Evaluation (Unseen Future Holdout)
> **Protocol Check:** The test set was accessed exactly once on the chosen champion model after selection.

| Metric | Test Value (Linear Regressor) | Validation Value | Delta (Test - Val) | Oracle Benchmark (Test) |
|---|---|---|---|---|
| **Mean Absolute Error (MAE)** | **5.645** | 5.869 | -0.224 | 5.627 |
| **Root Mean Squared Error (RMSE)** | **6.965** | 7.369 | -0.404 | 6.956 |
| **Coefficient of Determination ($R^2$)** | **0.5862** | 0.5633 | +0.0229 | 0.5872 |

- **Alignment with Oracle Benchmark:** The champion model's Test RMSE of **6.965** is within $0.009$ points of the theoretical Oracle error ceiling of **6.956**, confirming effective extraction of all learnable linear signal.

---

## 5. Model Interpretability, Coefficients, & Multicollinearity Audit
Standardized regression coefficients ($\beta_j$) reflect the change in productivity score per one standard deviation change in the predictor.
To evaluate physical alignment with the underlying generative formula, coefficients must be unstandardized via $b_j = \beta_j / \sigma_j$,
where $\sigma_j$ is the training-set standard deviation of predictor $j$.

### 5.1 Standardized vs. Unstandardized Physical Slopes
| Predictor Feature | Std Coef ($\beta_j$) | Training Scale ($\sigma_j$) | Unstandardized Slope ($b_j$) | True Formula Slope | Physical Interpretation & Recovery Status |
|---|---|---|---|---|---|
| `focus_duration_hours` | `+4.6668` | `1.4712` | `+3.1722` | `+4.00` | Collinear sharing with session & utilization ($b = +3.17$) |
| `interruption_count` | `-3.0976` | `1.8465` | `-1.6775` | `-1.50` | Direct match ($b = -1.68$ vs $-1.50$) |
| `sleep_hours` | `+3.0289` | `1.0075` | `+3.0064` | `+3.00` | Direct match ($b = +3.01$ vs $+3.00$) |
| `task_difficulty_avg` | `-1.8078` | `0.8705` | `-2.0768` | `-2.00` | Direct match ($b = -2.08$ vs $-2.00$) |
| `work_session_duration_hours` | `+1.2748` | `1.5579` | `+0.8183` | `0.00 (not in formula)` | Collinear proxy absorbing focus variance |
| `work_session_utilization` | `+0.5748` | `0.1110` | `+5.1801` | `0.00 (not in formula)` | Collinear proxy absorbing focus variance |
| `inactivity_duration_hours` | `-0.5619` | `0.6576` | `-0.8544` | `0.00 (not in formula)` | Near-zero empirical association |
| `inactivity_ratio` | `+0.5338` | `0.1251` | `+4.2685` | `0.00 (not in formula)` | Near-zero empirical association |
| `tasks_completed` | `-0.3322` | `1.5657` | `-0.2122` | `0.00 (not in formula)` | Near-zero empirical association |
| `is_weekend` | `-0.3310` | `0.4518` | `-0.7326` | `0.00 (not in formula)` | Near-zero empirical association |
| `day_of_week` | `+0.1797` | `2.0000` | `+0.0899` | `0.00 (not in formula)` | Near-zero empirical association |
| `perceived_stress` | `+0.1772` | `0.9388` | `+0.1887` | `0.00 (not in formula)` | Near-zero empirical association |

### 5.2 Multicollinearity and Coefficient Distribution
In the multivariate model, the estimated unstandardized slope for `focus_duration_hours` is **+3.172**, while the raw generative slope is **+4.000**.
This divergence occurs because `work_session_duration_hours` ($b = +0.818$) and `work_session_utilization` ($b = +5.180$) are derived from and collinear with focus duration.
Summing the slopes of focus duration and session duration ($3.172 + 0.818 = 3.990$) precisely accounts for the +4.0 generative weight.

When an isolated Ordinary Least Squares (OLS) model is fitted exclusively on the 4 true structural features (`focus_duration_hours`, `sleep_hours`, `interruption_count`, `task_difficulty_avg`), the estimated slopes recover the generative parameters almost exactly:
- `focus_duration_hours`: **+3.9580** (True: +4.00)
- `sleep_hours`: **+2.9473** (True: +3.00)
- `interruption_count`: **-1.6403** (True: -1.50)
- `task_difficulty_avg`: **-2.0589** (True: -2.00)
- Intercept: **18.8636** (True theoretical intercept with mean consistency 0.875: **17.625**)

> **Important Causal Disclaimer:** Standardized regression coefficients and unstandardized slopes indicate statistical associations
> under the observed joint distribution and multicollinearity structure. They do **not** establish causal mechanisms or guarantee
> that intervening on a feature in isolation will yield the indicated change in cognitive productivity.

---

## 6. Responsible AI & Research Limitations
1. **Synthetic Nature of Evidence:** All experimental conclusions are derived from synthetic simulated telemetries.
Performance demonstrates pipeline functionality and mathematical rule recovery, **not** real-world human predictive validity.
2. **No Clinical or Capability Judgment:** Predicted productivity scores reflect statistical estimates of proxy activity levels.
They must never be used to judge personal capability, intelligence, or worth, nor used for clinical diagnosis of burnout or cognitive impairment.
3. **Generalization Boundaries:** The chronological split evaluates forecasting future timeframes for the **same 50 simulated users**.
Generalization to completely unseen external users has not been demonstrated and requires separate cross-user benchmarking.
