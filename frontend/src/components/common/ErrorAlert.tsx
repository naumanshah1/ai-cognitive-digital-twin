import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface ErrorAlertProps {
  title?: string
  message: string
  errorCode?: string
  onRetry?: () => void
  details?: Record<string, unknown> | null
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'Request Encountered an Issue',
  message,
  errorCode,
  onRetry,
  details,
}) => {
  return (
    <div
      role="alert"
      className="rounded-xl border border-rose-200 bg-rose-50/80 p-4 text-rose-900 shadow-xs"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm text-rose-900">{title}</h3>
            {errorCode && (
              <span className="text-xs font-mono bg-rose-100 text-rose-700 px-2 py-0.5 rounded">
                {errorCode}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-rose-800 leading-relaxed">{message}</p>
          {details && Object.keys(details).length > 0 && (
            <div className="mt-2 text-xs bg-rose-100/70 p-2 rounded text-rose-900 font-mono overflow-x-auto">
              {JSON.stringify(details, null, 2)}
            </div>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-rose-700 hover:text-rose-900 bg-white border border-rose-300 hover:border-rose-400 px-3 py-1.5 rounded-lg shadow-2xs transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Request</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
