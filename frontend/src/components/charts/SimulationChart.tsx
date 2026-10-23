import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from 'recharts';
import { AlertCircle } from 'lucide-react';

interface SimulationChartProps {
  baselineScore: number;
  simulatedScore: number;
  metricName?: string;
}

export const SimulationChart: React.FC<SimulationChartProps> = ({
  baselineScore,
  simulatedScore,
  metricName = 'Productivity Score',
}) => {
  const delta = simulatedScore - baselineScore;
  const isPositive = delta >= 0;

  const chartData = [
    {
      name: 'Baseline (Empirical)',
      score: Number(baselineScore.toFixed(2)),
      fill: '#64748b',
    },
    {
      name: 'Simulated (Intervention)',
      score: Number(simulatedScore.toFixed(2)),
      fill: isPositive ? '#10b981' : '#f43f5e',
    },
  ];

  return (
    <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Baseline vs. Simulated Outcome
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Model-projected response under hypothetical behavioural parameter adjustments
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500">Projected Shift:</span>
          <span
            className={`text-xs font-bold px-2 py-0.5 rounded-full ${
              isPositive
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
                : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800'
            }`}
          >
            {isPositive ? `+${delta.toFixed(2)}` : delta.toFixed(2)} pts
          </span>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 0, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.2} />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#64748b' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(value: unknown) => [`${Number(value).toFixed(2)} / 100`, metricName]}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
            <Bar dataKey="score" name={metricName} radius={[6, 6, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Methodological / Non-Causal Disclaimer */}
      <div className="mt-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 flex items-start space-x-2 text-xs text-amber-800 dark:text-amber-300">
        <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden="true" />
        <p className="leading-tight">
          <strong>Scientific Notice:</strong> What-if simulations evaluate conditional predictions from the
          trained regression estimator ($y = f(x)$). These outputs represent hypothetical associations and
          do not prove real-world causality or clinical interventions.
        </p>
      </div>
    </div>
  );
};
