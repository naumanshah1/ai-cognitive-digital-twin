/**
 * Central Deterministic Demo Data Engine for Cognitive Twin
 * Generates realistic, reproducible 90-day synthetic telemetry and cross-module
 * consistent analytics across 5 distinct behavioral scenarios.
 */

export interface DailyTelemetry {
  date: string;
  dayOfWeek: string;
  isWeekend: boolean;
  focusHours: number;
  meetingHours: number;
  sleepHours: number;
  screenHours: number;
  interruptions: number;
  tasksPlanned: number;
  tasksCompleted: number;
  taskCompletionRate: number;
  productivityScore: number;
}

export interface DemoPersona {
  id: string;
  name: string;
  tagline: string;
  archetype: string;
  description: string;
  baseline: {
    meanFocusHours: number;
    meanMeetingHours: number;
    meanSleepHours: number;
    meanScreenHours: number;
    meanInterruptions: number;
    meanProductivityScore: number;
    stabilityIndex: number;
  };
  driftStatus: {
    status: 'OPTIMAL' | 'DRIFT_DETECTED' | 'STABLE';
    flaggedFeaturesCount: number;
    primaryFeature: string;
    ksStatistic: number;
    pValue: number;
    fdrQValue: number;
    psiScore: number;
    summary: string;
    featureComparison: Array<{
      feature: string;
      baselineMean: number;
      comparisonMean: number;
      changePct: number;
      ksStat: number;
      pValue: number;
      driftDetected: boolean;
    }>;
  };
  recommendations: Array<{
    id: string;
    category: 'FOCUS_ARCHITECTURE' | 'MEETING_HYGIENE' | 'RECOVERY_SLEEP' | 'DIGITAL_WELLBEING';
    priorityScore: number;
    priorityLabel: 'HIGH' | 'MEDIUM' | 'NORMAL';
    confidence: 'HIGH' | 'MEDIUM' | 'LOW';
    title: string;
    proposedAction: string;
    rationale: string;
    evidence: string;
    expectedImpact: string;
  }>;
  simulationBaseline: {
    focusHours: number;
    sleepHours: number;
    screenHours: number;
    interruptions: number;
    baselineProductivity: number;
  };
  sampleAgentHistory: Array<{
    id: string;
    requestId: string;
    userGoal: string;
    status: 'COMPLETED' | 'FAILED';
    executionLatency: number;
    provider: string;
    createdAt: string;
    summary: string;
    findingsCount: number;
    recommendationsCount: number;
    toolsCalled: Array<{ toolName: string; durationMs: number; status: string }>;
  }>;
}

/**
 * Deterministic pseudo-random number generator (Mulberry32)
 * Ensures reproducible values across refreshes and test suites without global Math.random variance.
 */
class DeterministicRNG {
  private state: number;

  constructor(seed: number) {
    this.state = seed;
  }

  next(): number {
    let t = (this.state += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  range(min: number, max: number): number {
    return min + this.next() * (max - min);
  }

  gaussian(mean: number, std: number): number {
    const u1 = Math.max(1e-6, this.next());
    const u2 = this.next();
    const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    return mean + z0 * std;
  }
}

/**
 * Generate 90 days of daily telemetry for a given persona profile
 */
export function generatePersonaTelemetry(personaId: string, daysCount: number = 90): DailyTelemetry[] {
  // Use unique deterministic seed per persona
  const seedMap: Record<string, number> = {
    balanced_work: 42,
    focus_fragmentation: 1337,
    high_meeting: 2026,
    changing_pattern: 8888,
    stable_pattern: 9999,
  };
  const rng = new DeterministicRNG(seedMap[personaId] || 42);

  const records: DailyTelemetry[] = [];
  const baseDate = new Date('2026-07-23');

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  for (let i = 0; i < daysCount; i++) {
    const d = new Date(baseDate);
    d.setDate(baseDate.getDate() + i);

    const dayOfWeek = dayNames[d.getDay()];
    const isWeekend = d.getDay() === 0 || d.getDay() === 6;

    let focus = 5.2;
    let meetings = 2.0;
    let sleep = 7.5;
    let screen = 6.5;
    let interruptions = 3;

    if (personaId === 'balanced_work') {
      focus = isWeekend ? rng.range(1.5, 3.0) : rng.gaussian(5.8, 0.4);
      meetings = isWeekend ? rng.range(0.0, 0.5) : rng.gaussian(1.8, 0.3);
      sleep = rng.gaussian(7.6, 0.3);
      screen = isWeekend ? rng.range(4.0, 5.5) : rng.gaussian(6.2, 0.4);
      interruptions = isWeekend ? Math.round(rng.range(0, 2)) : Math.round(rng.range(1, 3));
    } else if (personaId === 'focus_fragmentation') {
      focus = isWeekend ? rng.range(1.0, 2.0) : rng.gaussian(3.2, 0.6);
      meetings = isWeekend ? rng.range(0.0, 1.0) : rng.gaussian(2.6, 0.5);
      sleep = rng.gaussian(6.4, 0.6);
      screen = isWeekend ? rng.range(6.0, 8.0) : rng.gaussian(8.8, 0.7);
      interruptions = isWeekend ? Math.round(rng.range(3, 5)) : Math.round(rng.gaussian(7.2, 1.2));
    } else if (personaId === 'high_meeting') {
      focus = isWeekend ? rng.range(1.0, 2.5) : rng.gaussian(3.5, 0.5);
      meetings = isWeekend ? rng.range(0.0, 0.8) : rng.gaussian(4.7, 0.6);
      sleep = rng.gaussian(6.8, 0.4);
      screen = isWeekend ? rng.range(5.0, 7.0) : rng.gaussian(9.4, 0.5);
      interruptions = isWeekend ? Math.round(rng.range(1, 3)) : Math.round(rng.gaussian(5.0, 1.0));
    } else if (personaId === 'changing_pattern') {
      // Days 0-60: balanced; Days 61-90: significant drift
      const isShifted = i >= 60;
      if (!isShifted) {
        focus = isWeekend ? rng.range(1.5, 2.5) : rng.gaussian(5.5, 0.4);
        meetings = isWeekend ? 0 : rng.gaussian(2.0, 0.4);
        interruptions = isWeekend ? 1 : Math.round(rng.range(1, 3));
        screen = rng.gaussian(6.0, 0.4);
      } else {
        focus = isWeekend ? rng.range(0.8, 1.5) : rng.gaussian(3.6, 0.6);
        meetings = isWeekend ? 0 : rng.gaussian(3.8, 0.7);
        interruptions = isWeekend ? 3 : Math.round(rng.gaussian(6.5, 1.1));
        screen = rng.gaussian(8.6, 0.6);
      }
      sleep = isShifted ? rng.gaussian(6.3, 0.5) : rng.gaussian(7.4, 0.3);
    } else {
      // stable_pattern
      focus = isWeekend ? rng.range(2.0, 3.0) : rng.gaussian(6.2, 0.3);
      meetings = isWeekend ? 0 : rng.gaussian(1.4, 0.2);
      sleep = rng.gaussian(8.0, 0.25);
      screen = isWeekend ? rng.range(3.5, 5.0) : rng.gaussian(5.5, 0.3);
      interruptions = isWeekend ? 0 : Math.round(rng.range(0, 2));
    }

    focus = Math.max(0.5, Math.min(14.0, Number(focus.toFixed(1))));
    meetings = Math.max(0.0, Math.min(12.0, Number(meetings.toFixed(1))));
    sleep = Math.max(4.0, Math.min(12.0, Number(sleep.toFixed(1))));
    screen = Math.max(2.0, Math.min(16.0, Number(screen.toFixed(1))));
    interruptions = Math.max(0, Math.min(25, Math.round(interruptions)));

    const tasksPlanned = isWeekend ? Math.round(rng.range(1, 3)) : Math.round(rng.range(6, 12));
    const completionRate = Math.min(1.0, Math.max(0.4, rng.range(0.7, 0.95)));
    const tasksCompleted = Math.round(tasksPlanned * completionRate);

    // Heuristic synthetic ground truth equation matching Milestone 1 / data dictionary
    const latent =
      30.0 +
      4.0 * focus +
      3.0 * (sleep - 7.0) +
      2.0 * (1.0 - interruptions * 0.1) -
      1.5 * interruptions +
      rng.gaussian(0, 2.5);
    const productivityScore = Math.max(10.0, Math.min(99.0, Number(latent.toFixed(1))));

    records.push({
      date: d.toISOString().split('T')[0],
      dayOfWeek,
      isWeekend,
      focusHours: focus,
      meetingHours: meetings,
      sleepHours: sleep,
      screenHours: screen,
      interruptions,
      tasksPlanned,
      tasksCompleted,
      taskCompletionRate: Number(completionRate.toFixed(2)),
      productivityScore,
    });
  }

  return records;
}

/**
 * 5 Standard Professional Demonstration Personas
 */
export const DEMO_PERSONAS: Record<string, DemoPersona> = {
  balanced_work: {
    id: 'balanced_work',
    name: 'Balanced Work Pattern Scenario',
    tagline: 'High focus stability with sustainable meeting density and consistent rest.',
    archetype: 'Optimal Work Rhythm',
    description:
      'Demonstrates an individual maintaining structured deep work intervals, disciplined recovery sleep, and low task switching.',
    baseline: {
      meanFocusHours: 5.8,
      meanMeetingHours: 1.8,
      meanSleepHours: 7.6,
      meanScreenHours: 6.2,
      meanInterruptions: 2,
      meanProductivityScore: 78.5,
      stabilityIndex: 91.2,
    },
    driftStatus: {
      status: 'STABLE',
      flaggedFeaturesCount: 0,
      primaryFeature: 'focus_duration_hours',
      ksStatistic: 0.12,
      pValue: 0.74,
      fdrQValue: 0.81,
      psiScore: 0.04,
      summary:
        'No statistically significant covariate shifts detected over the 14-day reference vs 7-day test window.',
      featureComparison: [
        {
          feature: 'Focus Duration',
          baselineMean: 5.8,
          comparisonMean: 5.7,
          changePct: -1.7,
          ksStat: 0.12,
          pValue: 0.74,
          driftDetected: false,
        },
        {
          feature: 'Meeting Load',
          baselineMean: 1.8,
          comparisonMean: 1.9,
          changePct: +5.5,
          ksStat: 0.14,
          pValue: 0.65,
          driftDetected: false,
        },
        {
          feature: 'Task Interruptions',
          baselineMean: 2.1,
          comparisonMean: 2.2,
          changePct: +4.7,
          ksStat: 0.11,
          pValue: 0.82,
          driftDetected: false,
        },
        {
          feature: 'Sleep Duration',
          baselineMean: 7.6,
          comparisonMean: 7.5,
          changePct: -1.3,
          ksStat: 0.09,
          pValue: 0.89,
          driftDetected: false,
        },
      ],
    },
    recommendations: [
      {
        id: 'REC-BW-01',
        category: 'FOCUS_ARCHITECTURE',
        priorityScore: 0.52,
        priorityLabel: 'NORMAL',
        confidence: 'HIGH',
        title: 'Preserve Morning Deep-Work Protected Window',
        proposedAction: 'Maintain current 09:00 - 11:30 calendar block for uninterrupted deep work.',
        rationale: 'Observed telemetry confirms peak cognitive focus is concentrated in morning intervals.',
        evidence: 'Mean focus duration of 5.8 hrs/day is currently stable within cohort 85th percentile.',
        expectedImpact: 'Estimated +2% sustained cognitive output stability.',
      },
      {
        id: 'REC-BW-02',
        category: 'RECOVERY_SLEEP',
        priorityScore: 0.45,
        priorityLabel: 'NORMAL',
        confidence: 'HIGH',
        title: 'Maintain Consistent Weekend Sleep Wake Offset',
        proposedAction: 'Keep weekend sleep onset within 45 minutes of weekday schedule.',
        rationale: 'Consistency in sleep timing preserves circadian stability and day-ahead focus.',
        evidence: 'Telemetry demonstrates 7.6h sleep duration with low variance.',
        expectedImpact: 'Prevents Monday morning productivity dip.',
      },
    ],
    simulationBaseline: {
      focusHours: 5.8,
      sleepHours: 7.6,
      screenHours: 6.2,
      interruptions: 2,
      baselineProductivity: 78.5,
    },
    sampleAgentHistory: [
      {
        id: 'DEMO-RUN-01',
        requestId: 'REQ-DEMO-BW-01',
        userGoal: 'Analyze current baseline focus stability and evaluate whether drift is present.',
        status: 'COMPLETED',
        executionLatency: 1.24,
        provider: 'Gemini 2.5 Flash',
        createdAt: '2026-10-21T14:30:00Z',
        summary:
          'Baseline focus is highly stable at 5.8 hrs/day. Kolmogorov-Smirnov test yielded p=0.74, indicating absence of covariate shift.',
        findingsCount: 3,
        recommendationsCount: 2,
        toolsCalled: [
          { toolName: 'profile_user_behaviour', durationMs: 410, status: 'SUCCESS' },
          { toolName: 'detect_drift', durationMs: 520, status: 'SUCCESS' },
        ],
      },
    ],
  },

  focus_fragmentation: {
    id: 'focus_fragmentation',
    name: 'Focus Fragmentation Scenario',
    tagline: 'High interruptions and frequent multitasking causing fragmented deep work.',
    archetype: 'Attention Splitting',
    description:
      'Demonstrates an individual encountering frequent communication interruptions, elevated context switching, and reduced sustained focus.',
    baseline: {
      meanFocusHours: 3.2,
      meanMeetingHours: 2.6,
      meanSleepHours: 6.4,
      meanScreenHours: 8.8,
      meanInterruptions: 7,
      meanProductivityScore: 58.2,
      stabilityIndex: 62.4,
    },
    driftStatus: {
      status: 'DRIFT_DETECTED',
      flaggedFeaturesCount: 2,
      primaryFeature: 'interruption_count',
      ksStatistic: 0.41,
      pValue: 0.012,
      fdrQValue: 0.024,
      psiScore: 0.28,
      summary:
        'Statistically significant covariate shift detected in Task Interruptions (p=0.012) and Focus Duration (p=0.028).',
      featureComparison: [
        {
          feature: 'Task Interruptions',
          baselineMean: 4.2,
          comparisonMean: 7.4,
          changePct: +76.2,
          ksStat: 0.41,
          pValue: 0.012,
          driftDetected: true,
        },
        {
          feature: 'Focus Duration',
          baselineMean: 4.5,
          comparisonMean: 3.1,
          changePct: -31.1,
          ksStat: 0.38,
          pValue: 0.028,
          driftDetected: true,
        },
        {
          feature: 'Screen Time',
          baselineMean: 7.2,
          comparisonMean: 8.9,
          changePct: +23.6,
          ksStat: 0.29,
          pValue: 0.082,
          driftDetected: false,
        },
        {
          feature: 'Sleep Duration',
          baselineMean: 6.8,
          comparisonMean: 6.3,
          changePct: -7.3,
          ksStat: 0.22,
          pValue: 0.165,
          driftDetected: false,
        },
      ],
    },
    recommendations: [
      {
        id: 'REC-FF-01',
        category: 'FOCUS_ARCHITECTURE',
        priorityScore: 0.88,
        priorityLabel: 'HIGH',
        confidence: 'HIGH',
        title: 'Batch Digital Communication into Structured Intervals',
        proposedAction: 'Configure notification batching to 12:00 and 16:30 rather than continuous streaming.',
        rationale: 'Frequent context switching degrades working memory and reduces sustained focus blocks below 45 minutes.',
        evidence: 'Observed telemetry records 7.4 interruptions/hour, which is 85% above cohort baseline.',
        expectedImpact: 'Estimated +1.4 hrs/day of uninterrupted focus time.',
      },
      {
        id: 'REC-FF-02',
        category: 'DIGITAL_WELLBEING',
        priorityScore: 0.74,
        priorityLabel: 'HIGH',
        confidence: 'MEDIUM',
        title: 'Enforce Workstation App Whitelisting During Focus Sprints',
        proposedAction: 'Mute non-essential chat channels during designated 90-minute morning deep work blocks.',
        rationale: 'Telemetry indicates interruptions frequently lead to 15+ minutes of unplanned browsing.',
        evidence: 'Screen time expanded to 8.8 hrs/day with only 3.2 hrs deep work.',
        expectedImpact: 'Reduces task switching latency by an estimated 25%.',
      },
    ],
    simulationBaseline: {
      focusHours: 3.2,
      sleepHours: 6.4,
      screenHours: 8.8,
      interruptions: 7,
      baselineProductivity: 58.2,
    },
    sampleAgentHistory: [
      {
        id: 'DEMO-RUN-02',
        requestId: 'REQ-DEMO-FF-01',
        userGoal: 'Detect behavioural drift and generate corrective interventions for high interruption rate.',
        status: 'COMPLETED',
        executionLatency: 1.58,
        provider: 'Gemini 2.5 Flash',
        createdAt: '2026-10-21T11:15:00Z',
        summary:
          'Covariate shift confirmed in task interruptions (p=0.012). Agent synthesized notification batching and workstation whitelisting interventions.',
        findingsCount: 4,
        recommendationsCount: 2,
        toolsCalled: [
          { toolName: 'detect_drift', durationMs: 640, status: 'SUCCESS' },
          { toolName: 'generate_recommendations', durationMs: 780, status: 'SUCCESS' },
        ],
      },
    ],
  },

  high_meeting: {
    id: 'high_meeting',
    name: 'High Meeting Load Scenario',
    tagline: 'Excessive collaborative synchrony crowding out independent focus windows.',
    archetype: 'Meeting Saturation',
    description:
      'Demonstrates an individual spending nearly half their workday in meetings, leading to extended screen hours and late-day focus attempts.',
    baseline: {
      meanFocusHours: 3.5,
      meanMeetingHours: 4.7,
      meanSleepHours: 6.8,
      meanScreenHours: 9.4,
      meanInterruptions: 5,
      meanProductivityScore: 62.0,
      stabilityIndex: 68.1,
    },
    driftStatus: {
      status: 'DRIFT_DETECTED',
      flaggedFeaturesCount: 2,
      primaryFeature: 'meeting_duration_hours',
      ksStatistic: 0.44,
      pValue: 0.008,
      fdrQValue: 0.016,
      psiScore: 0.32,
      summary:
        'Statistically significant increase in Meeting Load (p=0.008, +48% vs baseline) detected by Kolmogorov-Smirnov test.',
      featureComparison: [
        {
          feature: 'Meeting Duration',
          baselineMean: 3.1,
          comparisonMean: 4.7,
          changePct: +51.6,
          ksStat: 0.44,
          pValue: 0.008,
          driftDetected: true,
        },
        {
          feature: 'Screen Time',
          baselineMean: 7.5,
          comparisonMean: 9.4,
          changePct: +25.3,
          ksStat: 0.36,
          pValue: 0.035,
          driftDetected: true,
        },
        {
          feature: 'Focus Duration',
          baselineMean: 4.4,
          comparisonMean: 3.5,
          changePct: -20.5,
          ksStat: 0.28,
          pValue: 0.095,
          driftDetected: false,
        },
      ],
    },
    recommendations: [
      {
        id: 'REC-HM-01',
        category: 'MEETING_HYGIENE',
        priorityScore: 0.92,
        priorityLabel: 'HIGH',
        confidence: 'HIGH',
        title: 'Establish Institutional Focus Wednesday (No-Meeting Day)',
        proposedAction: 'Designate Wednesday as an asynchronous work block free of recurring status syncs.',
        rationale: 'Consolidating meetings into specific days reclaims continuous multi-hour focus blocks.',
        evidence: 'Meeting duration currently averages 4.7 hrs/day, exceeding the 3.0h healthy threshold.',
        expectedImpact: 'Reclaims an estimated +3.2 hours of uninterrupted deep work per week.',
      },
      {
        id: 'REC-HM-02',
        category: 'MEETING_HYGIENE',
        priorityScore: 0.78,
        priorityLabel: 'HIGH',
        confidence: 'HIGH',
        title: 'Shorten Default Calendar Bookings to 25 / 50 Minutes',
        proposedAction: 'Enable speedier meetings setting to introduce mandatory 5-10 minute decompression buffers.',
        rationale: 'Back-to-back virtual meetings elevate cognitive load and deplete working memory.',
        evidence: 'Telemetry indicates zero recovery buffer between 70% of consecutive calendar events.',
        expectedImpact: 'Estimated 35% reduction in end-of-day cognitive fatigue.',
      },
    ],
    simulationBaseline: {
      focusHours: 3.5,
      sleepHours: 6.8,
      screenHours: 9.4,
      interruptions: 5,
      baselineProductivity: 62.0,
    },
    sampleAgentHistory: [
      {
        id: 'DEMO-RUN-03',
        requestId: 'REQ-DEMO-HM-01',
        userGoal: 'Simulate scenario impact of reducing meeting load by 2 hours and increasing focus by 1.5 hours.',
        status: 'COMPLETED',
        executionLatency: 1.45,
        provider: 'Gemini 2.5 Flash',
        createdAt: '2026-10-21T09:40:00Z',
        summary:
          'What-if scenario executed: Reducing meetings and expanding focus to 5.0 hrs increases estimated productivity score from 62.0 to 74.2 (+12.2 points).',
        findingsCount: 3,
        recommendationsCount: 2,
        toolsCalled: [
          { toolName: 'simulate_what_if', durationMs: 580, status: 'SUCCESS' },
          { toolName: 'generate_recommendations', durationMs: 650, status: 'SUCCESS' },
        ],
      },
    ],
  },

  changing_pattern: {
    id: 'changing_pattern',
    name: 'Changing Pattern (Drifting) Scenario',
    tagline: 'Recent behavioral inflection point showing longitudinal habit divergence.',
    archetype: 'Longitudinal Transition',
    description:
      'Demonstrates a user undergoing significant schedule alterations over the last 30 days, causing marked shifts in baseline parameters.',
    baseline: {
      meanFocusHours: 3.8,
      meanMeetingHours: 3.8,
      meanSleepHours: 6.3,
      meanScreenHours: 8.6,
      meanInterruptions: 6,
      meanProductivityScore: 60.5,
      stabilityIndex: 54.0,
    },
    driftStatus: {
      status: 'DRIFT_DETECTED',
      flaggedFeaturesCount: 3,
      primaryFeature: 'focus_duration_hours',
      ksStatistic: 0.52,
      pValue: 0.003,
      fdrQValue: 0.009,
      psiScore: 0.42,
      summary:
        'Pronounced multivariate covariate shift detected across Focus Duration (p=0.003), Sleep (p=0.015), and Interruptions (p=0.011).',
      featureComparison: [
        {
          feature: 'Focus Duration',
          baselineMean: 5.5,
          comparisonMean: 3.8,
          changePct: -30.9,
          ksStat: 0.52,
          pValue: 0.003,
          driftDetected: true,
        },
        {
          feature: 'Task Interruptions',
          baselineMean: 2.3,
          comparisonMean: 6.2,
          changePct: +169.5,
          ksStat: 0.48,
          pValue: 0.011,
          driftDetected: true,
        },
        {
          feature: 'Sleep Duration',
          baselineMean: 7.4,
          comparisonMean: 6.3,
          changePct: -14.8,
          ksStat: 0.42,
          pValue: 0.015,
          driftDetected: true,
        },
      ],
    },
    recommendations: [
      {
        id: 'REC-CP-01',
        category: 'FOCUS_ARCHITECTURE',
        priorityScore: 0.86,
        priorityLabel: 'HIGH',
        confidence: 'HIGH',
        title: 'Perform 14-Day Calendar Audit to Re-establish Baseline Focus',
        proposedAction: 'Decline low-priority ad-hoc obligations and schedule two daily 90-minute focus sessions.',
        rationale: 'Longitudinal shift detection flags steady decline in focus duration over past 30 days.',
        evidence: 'Focus dropped from 5.5 hrs to 3.8 hrs/day since shift onset.',
        expectedImpact: 'Stabilizes productivity score above 70 threshold.',
      },
    ],
    simulationBaseline: {
      focusHours: 3.8,
      sleepHours: 6.3,
      screenHours: 8.6,
      interruptions: 6,
      baselineProductivity: 60.5,
    },
    sampleAgentHistory: [
      {
        id: 'DEMO-RUN-04',
        requestId: 'REQ-DEMO-CP-01',
        userGoal: 'Evaluate longitudinal drift over 90 days and identify the temporal divergence date.',
        status: 'COMPLETED',
        executionLatency: 1.62,
        provider: 'Gemini 2.5 Flash',
        createdAt: '2026-10-20T16:00:00Z',
        summary:
          'Longitudinal shift point located at Day 61. KS statistic is 0.52 with BH-adjusted FDR q=0.009.',
        findingsCount: 4,
        recommendationsCount: 1,
        toolsCalled: [
          { toolName: 'detect_drift', durationMs: 720, status: 'SUCCESS' },
          { toolName: 'profile_user_behaviour', durationMs: 490, status: 'SUCCESS' },
        ],
      },
    ],
  },

  stable_pattern: {
    id: 'stable_pattern',
    name: 'Stable Pattern Scenario',
    tagline: 'High cognitive resilience with minimal daily variance and deep restorative sleep.',
    archetype: 'Peak Consistency',
    description:
      'Demonstrates an experienced deep worker with disciplined calendar boundaries, minimal interruptions, and high baseline productivity.',
    baseline: {
      meanFocusHours: 6.2,
      meanMeetingHours: 1.4,
      meanSleepHours: 8.0,
      meanScreenHours: 5.5,
      meanInterruptions: 1,
      meanProductivityScore: 84.0,
      stabilityIndex: 96.5,
    },
    driftStatus: {
      status: 'STABLE',
      flaggedFeaturesCount: 0,
      primaryFeature: 'focus_duration_hours',
      ksStatistic: 0.08,
      pValue: 0.88,
      fdrQValue: 0.92,
      psiScore: 0.02,
      summary:
        'All evaluated features demonstrate exceptional distribution stability. Kolmogorov-Smirnov p=0.88.',
      featureComparison: [
        {
          feature: 'Focus Duration',
          baselineMean: 6.2,
          comparisonMean: 6.3,
          changePct: +1.6,
          ksStat: 0.08,
          pValue: 0.88,
          driftDetected: false,
        },
        {
          feature: 'Meeting Duration',
          baselineMean: 1.4,
          comparisonMean: 1.3,
          changePct: -7.1,
          ksStat: 0.10,
          pValue: 0.81,
          driftDetected: false,
        },
        {
          feature: 'Sleep Duration',
          baselineMean: 8.0,
          comparisonMean: 8.0,
          changePct: 0.0,
          ksStat: 0.06,
          pValue: 0.94,
          driftDetected: false,
        },
      ],
    },
    recommendations: [
      {
        id: 'REC-SP-01',
        category: 'FOCUS_ARCHITECTURE',
        priorityScore: 0.35,
        priorityLabel: 'NORMAL',
        confidence: 'HIGH',
        title: 'Maintain Current Periodization Framework',
        proposedAction: 'Continue existing 90-minute focus cycles followed by 15-minute recovery intervals.',
        rationale: 'Current baseline places user in top 5th percentile of cognitive focus consistency.',
        evidence: 'Mean focus 6.2h, sleep 8.0h, stability index 96.5/100.',
        expectedImpact: 'Sustained peak cognitive output.',
      },
    ],
    simulationBaseline: {
      focusHours: 6.2,
      sleepHours: 8.0,
      screenHours: 5.5,
      interruptions: 1,
      baselineProductivity: 84.0,
    },
    sampleAgentHistory: [
      {
        id: 'DEMO-RUN-05',
        requestId: 'REQ-DEMO-SP-01',
        userGoal: 'Benchmark baseline cognitive resilience against cohort 90th percentile.',
        status: 'COMPLETED',
        executionLatency: 1.15,
        provider: 'Gemini 2.5 Flash',
        createdAt: '2026-10-21T08:00:00Z',
        summary:
          'Baseline stability confirmed at 96.5/100. All metrics within optimal bounds; no drift flagged.',
        findingsCount: 2,
        recommendationsCount: 1,
        toolsCalled: [
          { toolName: 'profile_user_behaviour', durationMs: 380, status: 'SUCCESS' },
        ],
      },
    ],
  },
};
