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
    primary: 'bg-gov-secondary hover:bg-yellow-500 text-gov-primary border border-gov-secondary hover:border-yellow-500 shadow-gov hover:shadow-gov-md',
    secondary: 'bg-transparent border border-gov-primary hover:bg-gov-primary hover:text-white text-gov-primary shadow-gov hover:shadow-gov-md',
    ghost: 'bg-transparent hover:bg-gov-background text-gov-text hover:text-gov-primary border border-transparent hover:border-gov-border',
    success: 'bg-gov-success hover:bg-green-600 text-white border border-gov-success hover:border-green-600 shadow-gov hover:shadow-gov-md',
    warning: 'bg-gov-warning hover:bg-yellow-600 text-gov-text border border-gov-warning hover:border-yellow-600 shadow-gov hover:shadow-gov-md',
    danger: 'bg-gov-danger hover:bg-red-600 text-white border border-gov-danger hover:border-red-600 shadow-gov hover:shadow-gov-md',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm rounded-md min-h-[36px]',
    md: 'px-4 py-2 text-sm rounded-md min-h-[44px]',
    lg: 'px-6 py-3 text-base rounded-md min-h-[48px]',
    xl: 'px-8 py-4 text-lg rounded-md min-h-[52px]',
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
