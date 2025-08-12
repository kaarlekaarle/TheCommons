import type { ReactNode } from 'react';

interface EmptyProps {
  icon?: ReactNode;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}

export default function Empty({ icon, title, subtitle, action }: EmptyProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      {icon && (
        <div className="w-12 h-12 mb-4 text-muted flex items-center justify-center">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      {subtitle && (
        <p className="text-sm text-muted mb-6 max-w-sm">{subtitle}</p>
      )}
      {action && (
        <div className="flex-shrink-0">
          {action}
        </div>
      )}
    </div>
  );
}
