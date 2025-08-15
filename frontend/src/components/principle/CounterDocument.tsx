import { useState } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import { principlesCopy } from '../../copy/principles';

interface CounterDocumentProps {
  content: string;
  onDevelopView?: () => void;
  loading?: boolean;
}

export default function CounterDocument({
  content,
  onDevelopView,
  loading = false
}: CounterDocumentProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (loading) {
    return (
      <Card className="p-6 bg-gray-50 border shadow-sm" data-testid="counter-doc-card">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-32 bg-gray-200 rounded"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </Card>
    );
  }

  const displayContent = isExpanded ? content : content.slice(0, 200);
  const needsExpansion = content.length > 200;

  return (
    <Card className="p-6 bg-gray-50 border shadow-sm" data-testid="counter-doc-card">
      <div className="prose prose-gray max-w-none">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {principlesCopy.counterDoc.title}
        </h3>

        <div className="text-gray-700 leading-relaxed mb-4">
          {displayContent}
          {needsExpansion && !isExpanded && '...'}
        </div>

        <div className="flex flex-col gap-2">
          {needsExpansion && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-blue-600 hover:text-blue-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded text-sm"
            >
              {isExpanded ? 'Show less' : principlesCopy.counterDoc.readMore}
            </button>
          )}

          {onDevelopView && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onDevelopView}
              className="w-full"
            >
              {principlesCopy.counterDoc.develop}
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
