# Behavioural Dataset — Provenance and Generation Protocol

## 1. Provenance Overview

- **Project Title:** AI Cognitive Digital Twin: An Autonomous Behavioural Intelligence System
- **Research Working Title:** AI Cognitive Digital Twin: An Agentic Framework for Behavioural Intelligence and Productivity Prediction
- **Institution:** Nagarjuna College of Engineering and Technology, Bengaluru, Karnataka, India
- **Research Team:** Anas Mirza Baig, Arcot Sadiq Basha, Atharv Bhardwaj, Nauman Shah
- **Dataset Version:** `0.1.0`
- **Generator Implementation:** `app.services.synthetic_data.generate_synthetic_data`
- **Default Random Seed:** `42` (NumPy `default_rng(seed)`)
- **Default Baseline Parameters:**
  - `n_users`: 50
  - `n_days`: 90 (daily records, from `2026-01-01` to `2026-03-31`)
  - Total records: 4,500 user-day observations

---

## 2. Generative Mechanisms and Assumptions

The synthetic generator models individual behavioural distributions with both stable person-level baselines and realistic day-to-day fluctuations:

1. **Individual Baselines:**
   - `sleep_baseline` $\sim \mathcal{N}(7.5, 0.6^2)$ hours
   - `focus_baseline` $\sim \mathcal{N}(4.5, 0.8^2)$ hours
   - `consistency` $\sim \mathcal{U}(0.75, 1.0)$

2. **Daily Observations:**
   - `sleep_hours` clipped to $[3.0, 11.0]$ with daily noise $\mathcal{N}(0, 0.8^2)$.
   - `focus_duration_hours` clipped to $[0.0, 12.0]$ conditioned on sleep duration:
     $$\text{focus} = \text{focus\_baseline} + \mathcal{N}(0, 1.2^2) + 0.25 \cdot (\text{sleep} - 7.0)$$
   - `work_session_duration_hours` $\in [\text{focus}, 16.0]$, ensuring work sessions enclose deep focus.
   - `inactivity_duration_hours` bounded by work session duration.
   - `interruption_count` $\sim \text{Poisson}(\max(0.5, 4.0 - 0.12 \cdot \text{focus}))$.
   - `tasks_planned` $\sim \text{DiscreteUniform}(3, 8)$.
   - `tasks_completed` $\sim \text{Binomial}(\text{tasks\_planned}, p_{\text{completion}})$, where $p_{\text{completion}}$ is conditioned on focus and sleep.

3. **Synthetic Target Rule:**
   $$\text{productivity\_score} = \text{clip}(30.0 + 4.0 \cdot \text{focus} + 3.0 \cdot (\text{sleep} - 7.0) + 3.0 \cdot \text{consistency} - 1.5 \cdot \text{interruptions} - 2.0 \cdot (\text{difficulty} - 3.0) + \mathcal{N}(0, 7.0), 0, 100)$$

---

## 3. Synthetic Missingness Mechanism

In real human behavioural monitoring, objective device telemetry (e.g., active window durations, screen times) has high capture fidelity, whereas subjective self-reports exhibit missingness.

The generator models Missing Completely at Random (MCAR) for subjective ratings:
- `sleep_quality`: 3% simulated missingness rate.
- `mood_score`: 15% simulated missingness rate.
- `perceived_stress`: 15% simulated missingness rate.

Missing values are represented explicitly as `NaN` (or `<NA>` in pandas nullable `Int64` format) and are never imputed with 0.

---

## 4. Controlled Shift Scenarios

To support future drift detection and change-point analysis in Milestone 4, the generator supports configurable scenarios:
- **`baseline`**: Standard stochastic variation across the full 90 days.
- **`stress_spike`**: For the final 30% of days, interruptions increase ($\lambda + 3$) and perceived stress increases (+1.2), simulating acute stress / crunch periods.
- **`focus_drop`**: For the final 30% of days, focus decreases (-1.5 hrs) and screen time increases (+1.5 hrs), simulating cognitive fatigue or distraction drift.

---

## 5. Scientific Limitations and Research Ethics Statement

1. **Synthetic Nature:** This dataset is completely simulated. The relationships between sleep, focus, interruptions, and productivity are assumed mathematical heuristics rather than empirical psychological discoveries.
2. **Evaluation Claims:** High model performance or low MSE/MAE on this dataset reflects algorithmic recovery of the heuristic formula, **not** genuine predictive accuracy regarding human psychology or workplace productivity.
3. **Privacy and Safety:** No actual human data, device monitoring logs, or personal identifiers are contained in this dataset. All identifiers (`synthetic_0001`, etc.) are pseudonymous programmatic artifacts.
4. **Transition to Empirical Data:** Real-world validation and public benchmark datasets (e.g., StudentLife, ExtraSensory) will be introduced in subsequent research milestones and reported strictly separately from synthetic experiments.
