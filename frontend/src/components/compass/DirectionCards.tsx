import { useState } from 'react';
import { Check } from 'lucide-react';
import Button from '../ui/Button';

export type Direction = { 
  id: string; 
  title: string; 
  description?: string; 
  votes?: number;
};

type Props = {
  directions: Direction[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onSubmit: (id: string) => Promise<void>;
  isSubmitting: boolean;
  disabled?: boolean; // when aligned
};

export default function DirectionCards({ 
  directions, 
  selectedId, 
  onSelect, 
  onSubmit, 
  isSubmitting, 
  disabled = false 
}: Props) {
  const [submittingId, setSubmittingId] = useState<string | null>(null);

  const handleSubmit = async (directionId: string) => {
    if (isSubmitting || disabled) return;
    
    setSubmittingId(directionId);
    try {
      await onSubmit(directionId);
    } finally {
      setSubmittingId(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, directionId: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (!disabled) {
        onSelect(directionId);
      }
    }
  };

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {directions.map((direction) => {
        const isSelected = selectedId === direction.id;
        const isSubmittingThis = submittingId === direction.id;
        
        return (
          <div
            key={direction.id}
            data-testid={`direction-card-${direction.id}`}
            className={`p-6 bg-white rounded-xl border transition-all duration-200 cursor-pointer ${
              isSelected 
                ? 'border-blue-500 bg-blue-50 shadow-md' 
                : 'border-gray-200 shadow-sm hover:shadow-md hover:border-gray-300'
            } ${disabled ? 'opacity-75 cursor-not-allowed' : ''}`}
            onClick={() => !disabled && onSelect(direction.id)}
            onKeyDown={(e) => handleKeyDown(e, direction.id)}
            tabIndex={disabled ? -1 : 0}
            role="button"
            aria-pressed={isSelected}
            aria-label={`Select ${direction.title} direction`}
          >
            <div className="flex items-start justify-between mb-3">
              <h3 
                className="text-lg font-semibold text-gray-900"
                data-testid={`direction-title-${direction.id}`}
              >
                {direction.title}
              </h3>
              {isSelected && (
                <div className="flex items-center justify-center w-6 h-6 bg-blue-500 rounded-full">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
            
            <p className="text-gray-700 mb-4 leading-relaxed">
              {direction.description || 'Choose this direction to align with the community\'s long-term vision.'}
            </p>
            
            <Button 
              variant={isSelected ? "primary" : "ghost"}
              onClick={(e) => {
                e.stopPropagation();
                handleSubmit(direction.id);
              }}
              disabled={disabled || isSubmitting}
              loading={isSubmittingThis}
              className="w-full justify-center"
              data-testid={`align-btn-${direction.id}`}
            >
              {isSelected ? "Aligned" : "Align with this direction"}
            </Button>
          </div>
        );
      })}
    </div>
  );
}
