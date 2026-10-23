import React from 'react'

interface MetricCardProps {
  title: string
  value: string | number
  subtext?: string
  subtitle?: string
  icon?: React.ComponentType<{ className?: string }> | React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'primary'
  statusVariant?: 'neutral' | 'success' | 'warning' | 'danger'
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtext,
  subtitle,
  icon,
  variant,
  statusVariant = 'neutral',
}) => {
  const displaySubtext = subtitle || subtext

  // Map statusVariant to colors
  let borderStyle = 'border-slate-200 dark:border-slate-800'
  let iconBg = 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'

  const effectiveVariant = variant || (
    statusVariant === 'success'
      ? 'success'
      : statusVariant === 'warning'
      ? 'warning'
      : statusVariant === 'danger'
      ? 'error'
      : 'default'
  )

  if (effectiveVariant === 'success') {
    borderStyle = 'border-emerald-200 dark:border-emerald-800/60'
    iconBg = 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400'
  } else if (effectiveVariant === 'warning') {
    borderStyle = 'border-amber-200 dark:border-amber-800/60'
    iconBg = 'bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400'
  } else if (effectiveVariant === 'error') {
    borderStyle = 'border-rose-200 dark:border-rose-800/60'
    iconBg = 'bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400'
  } else if (effectiveVariant === 'primary') {
    borderStyle = 'border-indigo-200 dark:border-indigo-800/60'
    iconBg = 'bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400'
  }

  const renderIcon = () => {
    if (!icon) return null
    if (React.isValidElement(icon)) {
      return icon
    }
    const IconComp = icon as React.ComponentType<{ className?: string }>
    return <IconComp className="w-5 h-5" />
  }

  return (
    <div
      className={`bg-white dark:bg-slate-900 rounded-xl border ${borderStyle} p-5 shadow-xs hover:shadow-md transition-shadow duration-200`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
            {title}
          </p>
          <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            {value}
          </div>
          {displaySubtext && (
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{displaySubtext}</p>
          )}
        </div>
        {icon && (
          <div className={`p-2.5 rounded-lg ${iconBg} shrink-0`}>
            {renderIcon()}
          </div>
        )}
      </div>
    </div>
  )
}
