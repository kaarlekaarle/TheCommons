import type { ReactNode } from 'react';
import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

interface ButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'ghost' | 'secondary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  className,
  disabled,
  onClick,
  type = 'button',
  ...props
}: ButtonProps) {
  const baseClasses = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus-ring disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    primary: 'bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white shadow-soft hover:shadow-medium border border-primary-500/20',
    secondary: 'bg-surface border border-border-600 hover:border-primary-500/50 text-muted-200 hover:text-white shadow-soft hover:shadow-medium',
    ghost: 'bg-transparent hover:bg-surface/50 text-muted-300 hover:text-white border border-transparent hover:border-border-600',
    success: 'bg-gradient-to-r from-success-600 to-success-500 hover:from-success-500 hover:to-success-400 text-white shadow-soft hover:shadow-medium border border-success-500/20',
    warning: 'bg-gradient-to-r from-warning-600 to-warning-500 hover:from-warning-500 hover:to-warning-400 text-white shadow-soft hover:shadow-medium border border-warning-500/20',
    danger: 'bg-gradient-to-r from-danger-600 to-danger-500 hover:from-danger-500 hover:to-danger-400 text-white shadow-soft hover:shadow-medium border border-danger-500/20',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm rounded-lg',
    md: 'px-4 py-2 text-sm rounded-xl',
    lg: 'px-6 py-3 text-base rounded-xl',
    xl: 'px-8 py-4 text-lg rounded-2xl',
  };
  
  const hoverEffect = 'hover:transform hover:translate-y-[-1px] active:translate-y-0';
  
  return (
    <button
      type={type}
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        hoverEffect,
        className
      )}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <Loader2 className="w-4 h-4 animate-spin mr-2" />
      )}
      {children}
    </button>
  );
}
