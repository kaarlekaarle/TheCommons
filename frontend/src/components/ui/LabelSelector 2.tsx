import React, { useState, useEffect } from 'react';
import type { Label } from '../../types';
import { listLabels } from '../../lib/api';
import { flags } from '../../config/flags';
import LabelChip from './LabelChip';

interface LabelSelectorProps {
  selectedLabels: Label[];
  onLabelsChange: (labels: Label[]) => void;
  maxLabels?: number;
  className?: string;
  disabled?: boolean;
}

export const LabelSelector: React.FC<LabelSelectorProps> = ({
  selectedLabels,
  onLabelsChange,
  maxLabels = 5,
  className = '',
  disabled = false
}) => {
  const [availableLabels, setAvailableLabels] = useState<Label[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!flags.labelsEnabled) return;
    
    const fetchLabels = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const labels = await listLabels();
        setAvailableLabels(labels);
      } catch (err) {
        setError('Failed to load labels');
        console.error('Error loading labels:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLabels();
  }, []);

  const filteredLabels = availableLabels.filter(label =>
    label.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
    !selectedLabels.some(selected => selected.id === label.id)
  );

  const handleLabelSelect = (label: Label) => {
    if (selectedLabels.length >= maxLabels) return;
    onLabelsChange([...selectedLabels, label]);
    setSearchTerm('');
  };

  const handleLabelRemove = (labelId: string) => {
    onLabelsChange(selectedLabels.filter(label => label.id !== labelId));
  };

  const handleLabelChipClick = (slug: string) => {
    // Find the label by slug and remove it
    const labelToRemove = selectedLabels.find(label => label.slug === slug);
    if (labelToRemove) {
      handleLabelRemove(labelToRemove.id);
    }
  };

  if (!flags.labelsEnabled) {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Topics (max {maxLabels})
        </label>
        
        {/* Selected labels */}
        {selectedLabels.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {selectedLabels.map(label => (
              <div key={label.id} className="relative">
                <LabelChip 
                  label={label} 
                  size="sm"
                  onClick={handleLabelChipClick}
                  className="pr-6"
                />
                <button
                  type="button"
                  onClick={() => handleLabelRemove(label.id)}
                  className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600"
                  disabled={disabled}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Search input */}
        {selectedLabels.length < maxLabels && (
          <div className="relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search topics..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={disabled || isLoading}
            />
            
            {/* Search results */}
            {searchTerm && filteredLabels.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
                {filteredLabels.map(label => (
                  <button
                    key={label.id}
                    type="button"
                    onClick={() => handleLabelSelect(label)}
                    className="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                    disabled={disabled}
                  >
                    {label.name}
                  </button>
                ))}
              </div>
            )}
            
            {searchTerm && filteredLabels.length === 0 && !isLoading && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-3 text-gray-500 text-sm">
                No topics found matching "{searchTerm}"
              </div>
            )}
          </div>
        )}

        {/* Error message */}
        {error && (
          <p className="text-red-600 text-sm mt-1">{error}</p>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <p className="text-gray-500 text-sm mt-1">Loading topics...</p>
        )}
      </div>
    </div>
  );
};

export default LabelSelector;
