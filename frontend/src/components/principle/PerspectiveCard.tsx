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
  showBadge?: boolean;
  badgeText?: string;
  isPrimary?: boolean;
  isSecondary?: boolean;
  trend7d?: number | null; // Trend percentage for the last 7 days
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
  alignButtonText,
  showBadge = false,
  badgeText,
  isPrimary = false,
  isSecondary = false,
  trend7d = null
}: PerspectiveCardProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onToggleExpanded();
    }
  };

  return (
    <div
      className={`bg-white rounded-xl border transition-all duration-200 ${
        isAligned
          ? 'border-green-200 bg-green-50/50 shadow-md p-6'
          : isPrimary
          ? 'border-blue-200 bg-blue-50/50 shadow-md ring-1 ring-blue-200 p-6'
          : isSecondary
          ? 'border-gray-200 shadow-sm p-4'
          : 'border-gray-200 shadow-sm hover:shadow-md hover:border-gray-300 p-6'
      }`}
      data-testid={`perspective-card-${type}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className={`font-semibold text-gray-900 ${isSecondary ? 'text-base' : 'text-lg'}`} data-testid={`perspective-title-${type}`}>
              {title}
            </h3>
            {trend7d !== null && trend7d !== 0 && (
              <Badge 
                variant="outline" 
                className="text-xs px-2 py-1"
                data-testid="trend-chip"
                aria-label={`Primary leaning change past 7 days: ${trend7d > 0 ? '+' : ''}${trend7d} percent`}
              >
                {trend7d > 0 ? '↑' : '↓'} {trend7d > 0 ? '+' : ''}{trend7d}% this week
              </Badge>
            )}
          </div>
          {showBadge && badgeText && (
            <Badge variant="default" className="text-xs" data-testid="community-view-badge">
              {badgeText}
            </Badge>
          )}
        </div>
        {isAligned && (
          <Badge variant="success" data-testid="aligned-badge">
            <Check className="w-3 h-3 mr-1" />
            Aligned
          </Badge>
        )}
      </div>

      {/* Summary - always visible */}
      <p className={`text-gray-700 mb-4 leading-relaxed ${isSecondary ? 'text-sm' : ''}`}>
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
        variant={isAligned ? "ghost" : isPrimary ? "primary" : "outline"}
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
