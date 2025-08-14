import { useState } from 'react';
import { Check } from 'lucide-react';
import Button from '../ui/Button';
import { compassCopy } from '../../copy/compass';
import type { Vote } from '../../types';

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
  myVote?: Vote | null;
  onChangeAlignment?: (nextDirectionId: string) => void;
};

export default function DirectionCards({
  directions,
  selectedId,
  onSelect,
  onSubmit,
  isSubmitting,
  disabled = false,
  myVote,
  onChangeAlignment
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
        const isAligned = myVote?.option_id === direction.id;

        return (
          <div
            key={direction.id}
            data-testid={`direction-card-${direction.id}`}
            className={`p-6 bg-white rounded-xl border transition-all duration-200 ${
              isAligned
                ? 'border-green-200 bg-green-50/50 shadow-md'
                : isSelected
                ? 'border-blue-500 bg-blue-50 shadow-md cursor-pointer'
                : 'border-gray-200 shadow-sm hover:shadow-md hover:border-gray-300 cursor-pointer'
            } ${disabled && !isAligned ? 'opacity-75 cursor-not-allowed' : ''}`}
            onClick={() => !disabled && !isAligned && onSelect(direction.id)}
            onKeyDown={(e) => !isAligned && handleKeyDown(e, direction.id)}
            tabIndex={disabled && !isAligned ? -1 : 0}
            role="button"
            aria-pressed={isSelected}
            aria-label={isAligned ? `Aligned with ${direction.title}` : `Select ${direction.title} direction`}
          >
            <div className="flex items-start justify-between mb-3">
              <h3
                className="text-lg font-semibold text-gray-900"
                data-testid={`direction-title-${direction.id}`}
              >
                {direction.title}
              </h3>
              {isAligned && (
                <div className="flex items-center gap-1 rounded-full bg-green-100 text-green-800 px-2 py-0.5 text-xs font-medium" data-testid="aligned-pill">
                  <Check className="w-3 h-3" aria-hidden="true" />
                  {compassCopy.alignedPill}
                </div>
              )}
              {isSelected && !isAligned && (
                <div className="flex items-center justify-center w-6 h-6 bg-blue-500 rounded-full">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </div>

            <p className="text-gray-700 mb-4 leading-relaxed">
              {direction.description || 'Choose this direction to align with the community\'s long-term vision.'}
            </p>

            {isAligned && (
              <div className="mb-4">
                <p className="text-gray-700 text-sm mb-3">
                  {compassCopy.alignedSubtext}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    disabled
                    className="flex-1 justify-center"
                    data-testid={`align-btn-${direction.id}`}
                    aria-disabled="true"
                  >
                    {compassCopy.alignedPill}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => {
                      onChangeAlignment?.(direction.id);
                    }}
                    disabled={isSubmitting}
                    className="text-blue-600 hover:text-blue-700"
                    data-testid={`change-alignment-btn-${direction.id}`}
                  >
                    {compassCopy.changeAlignment}
                  </Button>
                </div>
              </div>
            )}

            {!isAligned && (
              <Button
                variant={isSelected ? "primary" : "ghost"}
                onClick={() => {
                  handleSubmit(direction.id);
                }}
                disabled={disabled || isSubmitting}
                loading={isSubmittingThis}
                className="w-full justify-center"
                data-testid={`align-btn-${direction.id}`}
              >
                {isSelected ? "Align with this direction" : "Align with this direction"}
              </Button>
            )}

            {isAligned && (
              <span role="status" aria-live="polite" className="sr-only">
                Aligned with {direction.title}. {compassCopy.alignedSubtext}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
