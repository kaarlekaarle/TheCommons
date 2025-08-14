import React from 'react';
import { Link } from 'react-router-dom';
import type { Label } from '../../types';
import LabelChip from './LabelChip';
import { getTopicOverviewCached } from '../../lib/cache/topicOverviewCache';

interface LabelTileProps {
  label: Label;
  count?: number;
  onClick?: (slug: string) => void;
  className?: string;
}

export const LabelTile: React.FC<LabelTileProps> = ({ 
  label, 
  count,
  onClick, 
  className = ''
}) => {
  const handleClick = () => {
    if (onClick) {
      onClick(label.slug);
    }
  };

  const handleMouseEnter = () => {
    // Prefetch topic overview on hover
    getTopicOverviewCached(label.slug);
  };

  const handleFocus = () => {
    // Prefetch topic overview on focus
    getTopicOverviewCached(label.slug);
  };

  const tileContent = (
    <div 
      className={`
        bg-white border border-gray-200 rounded-lg p-4 
        hover:shadow-md hover:border-gray-300 
        focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2
        transition-all duration-200 cursor-pointer
        ${className}
      `}
      onClick={onClick ? handleClick : undefined}
      onMouseEnter={handleMouseEnter}
      onFocus={handleFocus}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
      aria-label={`Browse ${label.name}${count ? ` (${count} items)` : ''}`}
    >
      <div className="flex items-center justify-between mb-2">
        <LabelChip 
          label={label} 
          size="xl"
          className="flex-1 text-center"
        />
      </div>
      {count !== undefined && (
        <div className="text-sm text-gray-600 text-center">
          {count} {count === 1 ? 'item' : 'items'}
        </div>
      )}
    </div>
  );

  // If onClick is provided, use button behavior
  if (onClick) {
    return tileContent;
  }

  // Otherwise, use Link for navigation
  return (
    <Link
      to={`/t/${label.slug}`}
      className="block"
      onMouseEnter={handleMouseEnter}
      onFocus={handleFocus}
      aria-label={`Browse ${label.name}${count ? ` (${count} items)` : ''}`}
    >
      {tileContent}
    </Link>
  );
};

export default LabelTile;
