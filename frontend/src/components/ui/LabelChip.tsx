import React from 'react';
import type { Label } from '../../types';

interface LabelChipProps {
  label: Label;
  onClick?: (slug: string) => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  active?: boolean;
}

export const LabelChip: React.FC<LabelChipProps> = ({ 
  label, 
  onClick, 
  className = '',
  size = 'md',
  active = false
}) => {
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base'
  };

  const baseClasses = `
    inline-flex items-center rounded-full font-medium
    transition-colors duration-200
    ${sizeClasses[size]}
    ${onClick ? 'cursor-pointer' : ''}
    ${active ? 'bg-blue-600 text-white border-blue-600' : 'bg-blue-100 text-blue-800 border border-blue-200 hover:bg-blue-200 hover:border-blue-300'}
    ${className}
  `;

  const handleClick = () => {
    if (onClick) {
      onClick(label.slug);
    }
  };

  return (
    <span 
      className={baseClasses}
      onClick={handleClick}
      title={label.name}
    >
      {label.name}
    </span>
  );
};

export default LabelChip;
