import { Check } from 'lucide-react';
import Button from '../ui/Button';
import { Expandable } from './Expandable';
import { compassCopy } from '../../copy/compass';


export type Direction = {
  id: string;
  title: string;
  description?: string;
  votes?: number;
};

type Props = {
  title: string;
  summary: string;
  readMoreHeading: string;
  rationale: string[];
  counterHeading: string;
  counters: string[];
  direction?: Direction;
  aligned?: boolean;
  onAlign?: () => void;
  onChangeAlignment?: () => void;
  isSubmitting?: boolean;
  disabled?: boolean;
};

export default function DirectionCard({
  title,
  summary,
  readMoreHeading,
  rationale,
  counterHeading,
  counters,
  direction,
  aligned = false,
  onAlign,
  onChangeAlignment,
  isSubmitting = false,
  disabled = false
}: Props) {
  const handleAlign = () => {
    if (!disabled && !aligned && onAlign) {
      onAlign();
    }
  };

  const handleChangeAlignment = () => {
    if (onChangeAlignment) {
      onChangeAlignment();
    }
  };

  return (
    <div
      data-testid={`direction-card-${direction?.id || 'custom'}`}
      className={`p-6 bg-white rounded-xl border transition-all duration-200 ${
        aligned
          ? 'border-green-200 bg-green-50/50 shadow-md'
          : 'border-gray-200 shadow-sm hover:shadow-md hover:border-gray-300'
      } ${disabled && !aligned ? 'opacity-75 cursor-not-allowed' : ''}`}
    >
      <div className="flex items-start justify-between mb-3">
        <h3
          className="text-lg font-semibold text-gray-900"
          data-testid={`direction-title-${direction?.id || 'custom'}`}
        >
          {title}
        </h3>
        {aligned && (
          <div className="flex items-center gap-1 rounded-full bg-green-100 text-green-800 px-2 py-0.5 text-xs font-medium" data-testid="aligned-pill">
            <Check className="w-3 h-3" aria-hidden="true" />
            {compassCopy.alignedPill}
          </div>
        )}
      </div>

      <p className="text-sm text-gray-700 mb-4">{summary}</p>

      <Expandable summary="Read more" id={`direction-${direction?.id || 'custom'}-details`}>
        <h4 className="font-medium">{readMoreHeading}</h4>
        <ul className="list-disc pl-5 mt-1 space-y-1">
          {rationale.map((r, i) => <li key={i}>{r}</li>)}
        </ul>
        <h5 className="font-medium mt-3">{counterHeading}</h5>
        <ul className="list-disc pl-5 mt-1 space-y-1">
          {counters.map((c, i) => <li key={i}>{c}</li>)}
        </ul>
      </Expandable>

      {aligned && (
        <div className="mt-4">
          <p className="text-gray-700 text-sm mb-3">
            {compassCopy.alignedSubtext}
          </p>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              disabled
              className="flex-1 justify-center"
              data-testid={`align-btn-${direction?.id || 'custom'}`}
              aria-disabled="true"
            >
              {compassCopy.alignedPill}
            </Button>
            <Button
              variant="ghost"
              onClick={handleChangeAlignment}
              disabled={isSubmitting}
              className="text-blue-600 hover:text-blue-700"
              data-testid={`change-alignment-btn-${direction?.id || 'custom'}`}
            >
              {compassCopy.changeAlignment}
            </Button>
          </div>
        </div>
      )}

      {!aligned && (
        <Button
          variant="primary"
          onClick={handleAlign}
          disabled={disabled || isSubmitting}
          loading={isSubmitting}
          className="w-full justify-center mt-4"
          data-testid={`align-btn-${direction?.id || 'custom'}`}
        >
          Align with this direction
        </Button>
      )}

      {aligned && (
        <span role="status" aria-live="polite" className="sr-only">
          Aligned with {title}. {compassCopy.alignedSubtext}
        </span>
      )}
    </div>
  );
}
