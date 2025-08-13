import type { ReactNode } from 'react';
import clsx from 'clsx';

interface BadgeProps {
  children: ReactNode;
  variant?: 'success' | 'warning' | 'danger' | 'principle' | 'action' | 'default';
  className?: string;
}

export default function Badge({ 
  children, 
  variant = 'default', 
  className 
}: BadgeProps) {
  const variantClasses = {
    default: 'badge',
    principle: 'badge badge-principle',
    action: 'badge badge-action',
    success: 'badge bg-success-50 text-success-700 border-success-200',
    warning: 'badge bg-accent-50 text-accent-700 border-accent-200',
    danger: 'badge bg-red-50 text-red-700 border-red-200',
  };

  return (
    <span className={clsx(variantClasses[variant], className)}>
      {children}
    </span>
  );
}
