import type { ReactNode } from 'react';
import clsx from 'clsx';

interface BadgeProps {
  children: ReactNode;
  variant?: 'success' | 'warning' | 'danger' | 'default';
  className?: string;
}

export default function Badge({ 
  children, 
  variant = 'default', 
  className 
}: BadgeProps) {
  return (
    <span className={clsx('badge', `badge-${variant}`, className)}>
      {children}
    </span>
  );
}
