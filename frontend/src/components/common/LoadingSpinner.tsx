import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  fullHeight?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading data...',
  size = 'md',
  fullHeight = false,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const containerClasses = fullHeight
    ? 'min-h-[400px] flex flex-col items-center justify-center p-8'
    : 'flex flex-col items-center justify-center p-6';

  return (
    <div className={containerClasses} role="status" aria-live="polite">
      <Loader2
        className={`${sizeClasses[size]} animate-spin text-indigo-600 dark:text-indigo-400`}
        aria-hidden="true"
      />
      {message && (
        <p className="mt-3 text-sm font-medium text-slate-600 dark:text-slate-300">
          {message}
        </p>
      )}
      <span className="sr-only">{message || 'Loading'}</span>
    </div>
  );
};
