import React from 'react'

interface StatusBadgeProps {
  status: string
  label?: string
  size?: 'sm' | 'md'
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  size = 'md',
}) => {
  const norm = (status || '').toLowerCase()

  let style = 'bg-slate-100 text-slate-700 border-slate-200'
  let dot = 'bg-slate-400'

  if (['ok', 'ready', 'completed', 'success', 'connected'].includes(norm)) {
    style = 'bg-emerald-50 text-emerald-700 border-emerald-200'
    dot = 'bg-emerald-500'
  } else if (['partial', 'tentative_drift', 'warning'].includes(norm)) {
    style = 'bg-amber-50 text-amber-700 border-amber-200'
    dot = 'bg-amber-500'
  } else if (
    ['failed', 'unready', 'unreachable', 'rejected', 'error', 'disconnected'].includes(
      norm
    )
  ) {
    style = 'bg-rose-50 text-rose-700 border-rose-200'
    dot = 'bg-rose-500'
  } else if (['pending', 'running'].includes(norm)) {
    style = 'bg-blue-50 text-blue-700 border-blue-200'
    dot = 'bg-blue-500 animate-pulse'
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${style} ${padding}`}
      role="status"
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} aria-hidden="true" />
      <span>{label || status.toUpperCase()}</span>
    </span>
  )
}
