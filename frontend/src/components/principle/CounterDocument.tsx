import React, { useState } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import { principlesDocCopy } from '../../copy/principlesDoc';

interface CounterDocumentProps {
  content: string;
  onDevelopView: () => void;
  loading?: boolean;
}

export default function CounterDocument({ content, onDevelopView, loading = false }: CounterDocumentProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
          <div className="space-y-2 mb-4">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
          <div className="h-9 bg-gray-200 rounded w-32"></div>
        </div>
      </Card>
    );
  }

  const hasContent = content && content.trim().length > 0;
  const lines = content.split('\n');
  const shouldShowReadMore = lines.length > 5;
  const displayContent = isExpanded ? content : lines.slice(0, 5).join('\n');

  return (
    <Card className="p-6">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">
        {principlesDocCopy.counterDocTitle}
      </h3>

      {hasContent ? (
        <>
          <div className="prose prose-gray max-w-none mb-4">
            <div className="whitespace-pre-line text-gray-800">
              {displayContent}
            </div>
          </div>

          {shouldShowReadMore && (
            <Button
              variant="ghost"
              onClick={() => setIsExpanded(!isExpanded)}
              className="mb-4 px-0 text-blue-600 hover:text-blue-700"
              aria-expanded={isExpanded}
            >
              {isExpanded ? principlesDocCopy.readLess : principlesDocCopy.readMore}
            </Button>
          )}

          <Button
            variant="outline"
            onClick={onDevelopView}
            className="w-full"
          >
            {principlesDocCopy.developThisView}
          </Button>
        </>
      ) : (
        <div className="text-center py-8">
          <p className="text-gray-600 mb-4">
            No counter-document has been developed yet.
          </p>
          <Button
            variant="outline"
            onClick={onDevelopView}
            className="w-full"
          >
            {principlesDocCopy.developThisView}
          </Button>
        </div>
      )}
    </Card>
  );
}
