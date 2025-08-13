import React, { useState, useEffect } from 'react';
import type { Label } from '../../types';
import { listLabels } from '../../lib/api';
import { flags } from '../../config/flags';
import LabelChip from './LabelChip';

interface LabelFilterBarProps {
  activeSlug?: string | null;
  onChange: (slug: string | null) => void;
  className?: string;
}

export const LabelFilterBar: React.FC<LabelFilterBarProps> = ({
  activeSlug,
  onChange,
  className = ''
}) => {
  const [labels, setLabels] = useState<Label[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!flags.labelsEnabled) return;
    
    const fetchLabels = async () => {
      setIsLoading(true);
      try {
        const fetchedLabels = await listLabels();
        setLabels(fetchedLabels);
      } catch (err) {
        console.error('Error loading labels:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLabels();
  }, []);

  if (!flags.labelsEnabled) {
    return null;
  }

  const handleLabelClick = (slug: string) => {
    onChange(activeSlug === slug ? null : slug);
  };

  const handleClearAll = () => {
    onChange(null);
  };

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Filter by Topic</h3>
        {activeSlug && (
          <button
            type="button"
            onClick={handleClearAll}
            className="text-sm text-blue-600 hover:text-blue-800 underline"
          >
            Clear filter
          </button>
        )}
      </div>
      
      {isLoading ? (
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
          <span>Loading topics...</span>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {labels.map(label => (
            <LabelChip
              key={label.id}
              label={label}
              onClick={() => handleLabelClick(label.slug)}
              size="sm"
              className={activeSlug === label.slug ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default LabelFilterBar;
