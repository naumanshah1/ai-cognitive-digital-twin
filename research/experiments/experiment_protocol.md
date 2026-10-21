# Data Engineering Experiment Protocol & Verification Standards

## 1. Experimental Protocol Overview

This document specifies the rigorous engineering and validation protocol governing Milestone 2 (Dataset Engineering Pipeline) of the **AI Cognitive Digital Twin** project.

- **Institution:** Nagarjuna College of Engineering and Technology, Bengaluru, Karnataka, India
- **Research Team:** Anas Mirza Baig, Arcot Sadiq Basha, Atharv Bhardwaj, Nauman Shah
- **Pipeline Implementation:** `app.data_pipeline.pipeline.run_data_pipeline`

---

## 2. Standard Experimental Configurations

| Parameter | Development Baseline | Production Benchmark |
|---|---|---|
| `n_users` | 5 users | 50 users |
| `n_days` | 20 days | 90 days |
| Total observations | 100 user-day records | 4,500 user-day records |
| `start_date` | `2026-01-01` | `2026-01-01` |
| `seed` | `42` | `42` |
| Chronological split | 70% Train / 15% Val / 15% Test | 70% Train / 15% Val / 15% Test |
| Train date window | Days 1–14 | Days 1–63 |
| Validation date window | Days 15–17 | Days 64–76 |
| Test date window | Days 18–20 | Days 77–90 |

---

## 3. Data Integrity & Validation Standards

Every dataset entering or exiting the pipeline must pass automated schema validation (`app.services.data_validation`):

1. **Schema Adherence:** All 15 raw columns must exist with correct data types.
2. **Missingness:** Missing values are permitted only in optional rating columns (`sleep_quality`, `mood_score`, `perceived_stress`). Any missingness in primary behavioural metrics causes validation failure.
3. **Domain Constraints:** All metrics must satisfy physiological and logical bounds (e.g., $0 \le \text{sleep} \le 24$, $\text{completed} \le \text{planned}$, $\text{inactivity} \le \text{work\_session}$).
4. **Duplicate Prevention:** Uniqueness of the composite key `(user_id, record_date)` is strictly enforced.

---

## 4. Leakage Prevention Rules

1. **Target Isolation:** `productivity_score` is strictly segregated into target partitions (`y_train.csv`, `y_val.csv`, `y_test.csv`) and never enters predictor feature matrices ($X$).
2. **Target-Derived Segregation:** Features calculated from past productivity (`rolling_productivity_mean_7d`, `productivity_change_7d`) are excluded from model predictors.
3. **Lagged Rolling Windows:** All temporal rolling statistics must shift by 1 record (`shift(1)`) prior to aggregation, preventing current-day contamination.
4. **Split Directionality:** Splitting is purely chronological along global date boundaries. Validation and test records are strictly posterior to training records:
   $$\max(\text{Date}_{\text{train}}) < \min(\text{Date}_{\text{val}}) \le \max(\text{Date}_{\text{val}}) < \min(\text{Date}_{\text{test}})$$
5. **Freeze-Transform Preprocessing:** Imputation medians, IQR outlier bounds, and `StandardScaler` parameters are fitted exclusively on the training partition and applied without refitting to validation and test sets.

---

## 5. Verification & Reproducibility Checks

Before accepting any dataset export:
1. Re-running the pipeline with identical parameters and seed must generate identical binary hashes or DataFrame equality (`pd.testing.assert_frame_equal`).
2. The data quality report must report `is_valid: true` and 0 critical errors.
3. The data split report must report `date_overlap_detected: false`.
4. Output feature matrices must contain 0 remaining `NaN` values and exactly match the expected schema column order.
