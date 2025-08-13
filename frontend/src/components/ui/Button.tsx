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
    primary: 'bg-primary-600 hover:bg-primary-700 text-white border border-primary-600 hover:border-primary-700 shadow-card hover:shadow-card-md focus:ring-primary-500/50',
    secondary: 'bg-white border border-neutral-300 hover:bg-neutral-50 text-neutral-800 border-neutral-300 hover:border-neutral-400',
    ghost: 'bg-transparent hover:bg-primary-50 text-primary-700 hover:text-primary-800 border border-transparent',
    success: 'bg-success-600 hover:bg-success-700 text-white border border-success-600 hover:border-success-700 shadow-card hover:shadow-card-md',
    warning: 'bg-accent-500 hover:bg-accent-500/90 text-white border border-accent-500 hover:border-accent-500/90 shadow-card hover:shadow-card-md',
    danger: 'bg-red-600 hover:bg-red-700 text-white border border-red-600 hover:border-red-700 shadow-card hover:shadow-card-md',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm rounded-lg min-h-[44px]',
    md: 'px-4 py-2 text-sm rounded-lg min-h-[44px]',
    lg: 'px-6 py-3 text-base rounded-lg min-h-[48px]',
    xl: 'px-8 py-4 text-lg rounded-lg min-h-[52px]',
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
