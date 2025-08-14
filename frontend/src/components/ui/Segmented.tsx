import React from 'react';

interface SegmentedOption {
  value: string;
  label: string;
}

interface SegmentedProps {
  name: string;
  value: string;
  onChange: (value: string) => void;
  options: SegmentedOption[];
  className?: string;
}

export default function Segmented({
  name,
  value,
  onChange,
  options,
  className = ""
}: SegmentedProps) {
  return (
    <div
      className={`flex rounded-lg border border-gray-300 p-1 ${className}`}
      role="radiogroup"
      aria-label={name}
    >
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={`flex-1 px-3 py-1.5 text-sm rounded-md transition-colors ${
            value === option.value
              ? 'bg-blue-500 text-white shadow-sm'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
          role="radio"
          aria-checked={value === option.value}
          data-testid={`${name}-${option.value}`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
