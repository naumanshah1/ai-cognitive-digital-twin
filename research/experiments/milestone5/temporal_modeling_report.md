# Temporal Modelling and LSTM Evaluation — Research Report

## 1. Executive Summary & Core Scientific Finding
- **Task Definition:** Next-day productivity forecasting (predicting `productivity_score` at day $t+1$ using exclusively historical behavioural telemetries up to day $t$).
- **Selected Champion Model:** **LSTM (Lookback=14d)** (Selected strictly via Validation RMSE = 10.4764).
- **Locked Test Partition Evaluation:** MAE = **8.055**, RMSE = **10.123**, $R^2 = **0.1259**.

### Key Finding on LSTM Value-Add:
> **Honest Scientific Assessment:** While the **LSTM (Lookback=14d)** was selected via validation RMSE (10.476 vs Ridge 10.579), its test partition performance (Test RMSE = **10.123**, $R^2 = **0.1259**) provides **no material or practical advantage** over the much simpler Lagged Ridge Regression baseline (Test RMSE = **10.141**, $R^2 = **0.1227**), differing by merely **0.019 points** (< 0.2% relative difference). Furthermore, the primary 7-day lookback LSTM actually underperformed Lagged Ridge on the test set (10.175 vs 10.141).

This empirical result is scientifically grounded in the synthetic data-generating mechanism: daily behavioral telemetry (focus duration, sleep, interruptions) and stochastic noise $\mathcal{N}(0, 7.0)$ are generated conditionally independently around static user baselines. Without true auto-regressive Markov dynamics, non-linear momentum, or multi-day sequential trajectories in the synthetic generator, the expressive power of recurrent neural architectures offers no structural benefit over a regularized linear model capturing recent user levels.

---

## 2. Formal Problem Formulation & Temporal Boundary Rules

### 2.1 Genuine Future-Prediction Task Definition
- **Forecast Origin ($t$):** At 23:59 on day $t$, daily telemetry logs are finalized.
- **Forecast Target ($t+1$):** Predict continuous productivity `productivity_score` on day $t+1$.
- **Permissible Inputs:**
  1. Historical daily behavioural metrics for days $\tau \in [t - L + 1, t]$.
  2. Historical engineered features available at day $\tau \le t$.
  3. Historical observed `productivity_score` for past days $\tau \le t$ (past observed ground truths).
- **Strict Leakage Prohibitions:**
  - The target $y(t+1)$ is **strictly prohibited** from entering the input window.
  - Same-day telemetries for day $t+1$ (e.g. tomorrow's focus hours, sleep, interruptions, tasks completed) are strictly unavailable at forecast time.

### 2.2 Distinction from Milestone 4 Retrospective Estimation
| Attribute | Milestone 4 (Diagnostic Assessment) | Milestone 5 (Prognostic Forecasting) |
|---|---|---|
| **Temporal Mode** | End-of-day retrospective estimation | Day-ahead forward forecasting |
| **Target Timestamp** | Day $t$ (`productivity_score` at $t$) | Day $t+1$ (`productivity_score` at $t+1$) |
| **Contemporaneous Predictors** | Same-day focus, sleep, interruptions ($t$) | **None** (tomorrow's behavior is unobserved) |
| **Signal Nature** | Direct structural formula recovery | Auto-regressive & historical user level tracking |
| **Test Performance Reference** | Test RMSE = **6.965**, $R^2 = **0.5862** | Test RMSE = **10.135**, $R^2 = **0.1238** (Lagged Ridge) |

> **Methodological Caveat:** Milestone 4 test metrics cannot and must not be compared to Milestone 5 as a forecasting baseline. Milestone 4 measures retrospective proxy inference with full same-day telemetries, whereas Milestone 5 measures true future forecasting.

---

## 3. Dataset, Sequence Construction, & Partition Boundaries

### 3.1 Chronological Partitions and Context Preservation
The evaluation population comprises the reproducible benchmark of **50 users across 90 calendar days** (4,500 total user-days, seed 42):
- **Training Period:** `2026-01-01` to `2026-03-04` (63 calendar days, 3,150 raw records).
- **Validation Period:** `2026-03-05` to `2026-03-17` (13 calendar days, 650 raw records).
- **Test Period:** `2026-03-18` to `2026-03-31` (14 calendar days, 700 raw records).

### 3.2 Sequence Counts across Lookback Horizons
| Split Partition | Target Date Range | Raw Calendar Days | Primary ($L=7$d) Sequences | Alternative ($L=14$d) Sequences |
|---|---|---|---|---|
| **Training** | `2026-01-08` to `2026-03-04` | 63 days | **2,800** | **2,450** |
| **Validation** | `2026-03-05` to `2026-03-17` | 13 days | **650** | **650** |
| **Test** | `2026-03-18` to `2026-03-31` | 14 days | **700** | **700** |

### 3.3 Split Boundary Context & Daily Continuity Rule
1. **Preceding Historical Context:** The first validation target (`2026-03-05`) uses historical inputs from the final 7 days of training. Similarly, the first test target (`2026-03-18`) uses inputs from the final 7 days of validation. This provides full historical context without leaking target labels.
2. **Daily Continuity Enforcement:** Sequence construction strictly checks that $date_{\tau} - date_{\tau-1} = 1$ day. Gaps or date skips are rejected.
3. **Zero Cross-User Leakage:** Sequences are strictly grouped by user; windows never span across user boundaries.

---

## 4. Forecasting Model Comparison & Empirical Results

### 4.1 Comprehensive Performance Table
All candidate forecasting models were evaluated on the **exact same 650 validation targets and 700 test targets**:

| Model Architecture | Lookback ($L$) | Val MAE | Val RMSE | Val $R^2$ | Test MAE | Test RMSE | Test $R^2$ | Model Category |
|---|---|---|---|---|---|---|---|---|
| **Training-Mean Baseline** | — | 8.997 | 11.182 | -0.0058 | 8.595 | 10.842 | -0.0028 | Constant Baseline |
| **Lag-1 Persistence Baseline** | 1d | 11.721 | 14.687 | -0.7349 | 10.994 | 13.799 | -0.6244 | Naive Temporal |
| **Lagged Ridge Regression** | 7d | **8.497** | **10.579** | **0.0997** | **8.072** | **10.141** | **0.1227** | Linear Regularized |
| **PyTorch LSTM (Primary)** | 7d | 8.516 | 10.584 | 0.0989 | 8.075 | 10.175 | 0.1169 | Recurrent Neural Net |
| **PyTorch LSTM (Alternative)** | 14d | 8.369 | 10.476 | 0.1172 | 8.055 | 10.123 | 0.1259 | Recurrent Neural Net |

### 4.2 Detailed Analysis of Baseline Behaviors
1. **Training-Mean Baseline ($R^2 \approx 0.00$):** Predicting the static training mean ($47.05$) yields an out-of-sample RMSE equal to the target population standard deviation ($10.842$).
2. **Lag-1 Persistence Baseline ($R^2 = -0.6244$):** Using yesterday's productivity score ($y_t$) to predict tomorrow ($y_{t+1}$) performs poorly because daily productivity is not a random walk. With i.i.d. daily noise and fluctuations, $\mathbb{E}[(y_{t+1} - y_t)^2] \approx 2 \text{Var}(y)$, producing an RMSE of $13.799$.
3. **Lagged Ridge Regression ($R^2 = 0.1238$):** Using the feature vector at origin $t$ and 7-day window averages extracts the stable user baseline effect, reducing Test RMSE to $10.135$.
4. **PyTorch LSTM:** With lookback $L=7$, the LSTM achieved Test RMSE = 10.175 ($R^2 = 0.1169$). Increasing lookback to $L=14$ resulted in Test RMSE = 10.123.

---

## 5. Model Selection & Overfitting Diagnostics
- **Selection Criterion:** Validation RMSE minimization on unseen chronological validation data.
- **Champion Selection:** **LSTM (Lookback=14d)** achieved the lowest Validation RMSE (**10.4764**).
- **Early Stopping in LSTM:** The primary LSTM completed training with early stopping at epoch **3**, successfully restoring the best validation checkpoint.

---

## 6. Responsible AI & Research Limitations
1. **Synthetic Nature of Evidence:** Experimental findings reflect synthetic telemetry generated by programmed heuristics. Performance verifies pipeline logic, **not** clinical or real-world human behavioral predictability.
2. **No Capability or Diagnostic Judgment:** Forecasted productivity scores represent statistical proxy estimates. They must never be interpreted as individual intelligence, capability, or clinical burnout diagnosis.
3. **Generalization Scope:** The evaluation tests day-ahead forecasting for the **same 50 simulated individuals** across time. Generalization to entirely unseen individuals requires a separate cross-user split.
4. **Scientific Value of Negative Results:** Acknowledging that LSTMs do not outperform simple regularized linear baselines on this dataset is an essential scientific conclusion, preventing premature over-engineering in downstream twin modules.
