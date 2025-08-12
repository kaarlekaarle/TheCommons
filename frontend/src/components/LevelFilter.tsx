import React from 'react';
import { Compass, Target, Layers } from 'lucide-react';

export type LevelFilterType = 'all' | 'level_a' | 'level_b';

interface LevelFilterProps {
  activeFilter: LevelFilterType;
  onFilterChange: (filter: LevelFilterType) => void;
  className?: string;
}

export default function LevelFilter({ activeFilter, onFilterChange, className = '' }: LevelFilterProps) {
  const filters = [
    {
      value: 'all' as const,
      label: 'All',
      icon: <Layers className="w-4 h-4" />,
      description: 'Show everything'
    },
    {
      value: 'level_a' as const,
      label: 'Principles',
      icon: <Compass className="w-4 h-4" />,
      description: 'Long-term direction'
    },
    {
      value: 'level_b' as const,
      label: 'Actions',
      icon: <Target className="w-4 h-4" />,
      description: 'Immediate decisions'
    }
  ];

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {filters.map((filter) => {
        const isActive = activeFilter === filter.value;
        const isLevelA = filter.value === 'level_a';
        const isLevelB = filter.value === 'level_b';
        
        // Color schemes for different levels
        let buttonClass = 'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200';
        
        if (isActive) {
          if (isLevelA) {
            buttonClass += ' bg-gov-primary text-white border border-gov-primary shadow-gov';
          } else if (isLevelB) {
            buttonClass += ' bg-gov-secondary text-gov-primary border border-gov-secondary shadow-gov';
          } else {
            buttonClass += ' bg-gov-text text-white border border-gov-text shadow-gov';
          }
        } else {
          buttonClass += ' bg-gov-surface border border-gov-border text-gov-text-muted hover:text-gov-text hover:border-gov-border-dark hover:bg-gov-background';
        }

        return (
          <button
            key={filter.value}
            onClick={() => onFilterChange(filter.value)}
            className={buttonClass}
            title={filter.description}
          >
            {filter.icon}
            <span>{filter.label}</span>
          </button>
        );
      })}
    </div>
  );
}
