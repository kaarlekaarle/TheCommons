import type { ReactNode } from 'react';
import clsx from 'clsx';
import type { BadgeVariant } from './types';

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export default function Badge({
  children,
  variant = 'default',
  className
}: BadgeProps) {
  const variantClasses: Record<BadgeVariant, string> = {
    default: 'badge',
    success: 'badge bg-success-50 text-success-700 border-success-200',
    warning: 'badge bg-accent-50 text-accent-700 border-accent-200',
    danger: 'badge bg-red-50 text-red-700 border-red-200',
    outline: 'badge border border-gray-300 bg-transparent text-gray-700',
  };

  return (
    <span className={clsx(variantClasses[variant], className)}>
      {children}
    </span>
  );
}
