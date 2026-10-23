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
} from 'recharts';

export interface MetricDataPoint {
  metric: string;
  value: number;
  unit?: string;
  benchmark?: number;
}

interface BehaviourChartProps {
  data: MetricDataPoint[];
  title?: string;
  description?: string;
}

export const BehaviourChart: React.FC<BehaviourChartProps> = ({
  data,
  title = 'Observed Behavioural Metrics',
  description = 'Baseline empirical metrics aggregated from synthetic telemetry',
}) => {
  // Validate and clean data
  const validData = data.filter(
    (item) => typeof item.value === 'number' && !isNaN(item.value) && isFinite(item.value)
  );

  if (validData.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-slate-500 border rounded-xl bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
        No valid numeric behavioural metrics available for visualization.
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
        {description && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{description}</p>
        )}
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={validData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.2} />
            <XAxis
              dataKey="metric"
              tick={{ fontSize: 11, fill: '#64748b' }}
              interval={0}
              angle={-20}
              textAnchor="end"
            />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(val: unknown) => [
                typeof val === 'number' ? Number(val).toFixed(2) : String(val),
                'Observed Value',
              ]}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
            <Bar dataKey="value" name="Observed Value" fill="#6366f1" radius={[4, 4, 0, 0]} />
            {validData.some((d) => d.benchmark !== undefined) && (
              <Bar dataKey="benchmark" name="Cohort Benchmark" fill="#94a3b8" radius={[4, 4, 0, 0]} />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 text-[11px] text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-2 flex items-center justify-between">
        <span>Units correspond to individual metrics (hours, scores, or counts).</span>
        <span>Recharts Visualizer</span>
      </div>
    </div>
  );
};
