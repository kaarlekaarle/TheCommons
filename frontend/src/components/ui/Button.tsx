import type { ReactNode } from 'react';
import clsx from 'clsx';
import { Loader2 } from 'lucide-react';
import type { ButtonVariant, ButtonSize } from './types';

interface ButtonProps {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
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

  const variantClasses: Record<ButtonVariant, string> = {
    primary: 'btn-primary hover:bg-primary-700 border border-primary-600 hover:border-primary-700 shadow-card hover:shadow-card-md focus:ring-primary-500/50',
    secondary: 'bg-surface border border-aa hover:bg-surface-muted text-strong border-aa hover:border-aa',
    ghost: 'bg-transparent hover:bg-primary-50 text-primary-700 hover:text-primary-800 border border-transparent',
    destructive: 'bg-red-600 hover:bg-red-700 text-white border border-red-600 hover:border-red-700 shadow-card hover:shadow-card-md',
    link: 'bg-transparent hover:bg-primary-50 text-primary-700 hover:text-primary-800 border border-transparent underline',
  };

  const sizeClasses: Record<ButtonSize, string> = {
    sm: 'px-3 py-1.5 text-sm rounded-lg min-h-[44px]',
    md: 'px-4 py-2 text-sm rounded-lg min-h-[44px]',
    lg: 'px-6 py-3 text-base rounded-lg min-h-[48px]',
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
