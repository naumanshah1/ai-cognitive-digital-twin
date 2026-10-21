# Behavioural Clustering — Feature Selection & Leakage Rationale

## 1. Unsupervised Clustering Philosophy
Clustering in the AI Cognitive Digital Twin is purely unsupervised exploratory discovery.
Its objective is to uncover latent, natural behavioural regimes (in daily records) and
phenotypical working styles (in user-level profiles) without any supervision from target labels.

## 2. Selected Feature Sets

### 2.1 Experiment A: Daily Record Clustering Features (10 Features)
| Feature Name | Theoretical Role | Range | Handling |
|---|---|---|---|
| `sleep_hours` | Recovery & rest proxy | [3.0, 11.0] | Standardized |
| `focus_duration_hours` | Deep work volume | [0.0, 12.0] | Standardized |
| `screen_time_hours` | Digital exposure | [0.0, 16.0] | Standardized |
| `task_difficulty_avg` | Cognitive complexity | [1.0, 5.0] | Standardized |
| `work_session_duration_hours` | Gross work window | [0.0, 16.0] | Standardized |
| `inactivity_duration_hours` | Idleness/fatigue proxy | [0.0, 16.0] | Standardized |
| `interruption_count` | Context-switching friction | [0, 20+] | Standardized |
| `task_completion_rate` | Daily execution efficiency | [0.0, 1.0] | Standardized (median imputed) |
| `work_session_utilization` | Proportion of session in deep focus | [0.0, 1.0] | Standardized |
| `inactivity_ratio` | Proportion of session inactive | [0.0, 1.0] | Standardized |

### 2.2 Experiment B: User-Level Aggregated Features (8 Features)
| Feature Name | Aggregation Method | Behavioural Interpretation |
|---|---|---|
| `mean_focus_hours` | Mean over 90 days | Baseline sustained focus capacity |
| `mean_sleep_hours` | Mean over 90 days | Baseline physiological recovery |
| `mean_screen_time_hours` | Mean over 90 days | Chronic digital exposure baseline |
| `mean_work_session_hours` | Mean over 90 days | Habitual work session length |
| `mean_task_completion_rate`| Mean over 90 days | Characteristic execution reliability |
| `mean_interruption_count` | Mean over 90 days | Characteristic disruption vulnerability |
| `focus_variability_std` | Standard deviation over 90 days | Routine stability vs. volatility |
| `work_session_consistency`| Proportion of days with >0 sessions | Routine commitment / discipline |

## 3. Excluded Columns & Leakage Rationale
| Excluded Column | Reason for Exclusion |
|---|---|
| `productivity_score` | Ground-truth prediction target. Including it in unsupervised clustering would cause catastrophic target leakage and circular cluster validation. |
| `rolling_productivity_mean_7d` | Derived from historical productivity scores. Excluded to prevent target leakage. |
| `productivity_change_7d` | Derived from historical productivity scores. Excluded to prevent target leakage. |
| `user_id` | Pseudonymous categorical identifier. Treating user IDs as numerical metrics would artificially group users by arbitrary string order. |
| `record_date` | Temporal timestamp. Excluded from clustering space to ensure clusters reflect behavioural patterns rather than calendar dates. |
| `day_of_week` | Calendar feature. Excluded from core behavioural distance metric to cluster intrinsic behavioural intensity rather than weekday/weekend scheduling. |
| `is_weekend` | Binary calendar feature. Excluded for same reason as day_of_week. |
| `mood_score` | Subjective self-report with 15% missingness. Excluded from baseline clustering to prevent distortion from synthetic MCAR imputation in distance metrics. |
| `perceived_stress` | Subjective self-report with 15% missingness. Excluded from baseline clustering to ensure distance metrics reflect objective telemetries. |
| `sleep_quality` | Subjective self-report rating. Excluded from distance metric in favor of objective sleep_hours. |