import React, { useState } from 'react';
import { Check } from 'lucide-react';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

interface PerspectiveCardProps {
  type: 'primary' | 'alternate';
  title: string;
  summary: string;
  longBody: string;
  isAligned: boolean;
  isSubmitting: boolean;
  onAlign: () => void;
  onToggleExpanded: () => void;
  isExpanded: boolean;
  readMoreText: string;
  readLessText: string;
  alignButtonText: string;
}

export default function PerspectiveCard({
  type,
  title,
  summary,
  longBody,
  isAligned,
  isSubmitting,
  onAlign,
  onToggleExpanded,
  isExpanded,
  readMoreText,
  readLessText,
  alignButtonText
}: PerspectiveCardProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onToggleExpanded();
    }
  };

  return (
    <div
      className={`p-6 bg-white rounded-xl border transition-all duration-200 ${
        isAligned
          ? 'border-green-200 bg-green-50/50 shadow-md'
          : 'border-gray-200 shadow-sm hover:shadow-md hover:border-gray-300'
      }`}
      data-testid={`perspective-card-${type}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900" data-testid={`perspective-title-${type}`}>
          {title}
        </h3>
        {isAligned && (
          <Badge variant="success" data-testid="aligned-badge">
            <Check className="w-3 h-3 mr-1" />
            Aligned
          </Badge>
        )}
      </div>

      {/* Summary - always visible */}
      <p className="text-gray-700 mb-4 leading-relaxed">
        {summary}
      </p>

      {/* Read more toggle */}
      <button
        onClick={onToggleExpanded}
        onKeyDown={handleKeyDown}
        className="text-blue-600 hover:text-blue-800 font-medium text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/60 focus:ring-offset-2 rounded mb-4"
        aria-expanded={isExpanded}
        aria-controls={`perspective-body-${type}`}
        data-testid={`read-more-toggle-${type}`}
      >
        {isExpanded ? readLessText : readMoreText}
      </button>

      {/* Long body - expandable */}
      {isExpanded && (
        <div
          id={`perspective-body-${type}`}
          className="mb-4 text-gray-700 leading-relaxed whitespace-pre-line"
          data-testid={`perspective-body-${type}`}
        >
          {longBody}
        </div>
      )}

      {/* Alignment button */}
      <Button
        variant={isAligned ? "ghost" : "primary"}
        onClick={onAlign}
        disabled={isSubmitting}
        loading={isSubmitting}
        className="w-full justify-center"
        data-testid={`align-button-${type}`}
      >
        {alignButtonText}
      </Button>
    </div>
  );
}
