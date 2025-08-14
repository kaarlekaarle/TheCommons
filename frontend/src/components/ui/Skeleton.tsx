import React from 'react';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  'data-testid'?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ 
  className = '', 
  width, 
  height,
  'data-testid': testId
}) => {
  const style: React.CSSProperties = {};
  
  if (width) {
    style.width = typeof width === 'number' ? `${width}px` : width;
  }
  
  if (height) {
    style.height = typeof height === 'number' ? `${height}px` : height;
  }
  
  return (
    <div
      className={`animate-pulse bg-gray-200 rounded ${className}`}
      style={style}
      data-testid={testId}
      aria-hidden="true"
    />
  );
};

export const SkeletonCard: React.FC<{ 'data-testid'?: string }> = ({ 'data-testid': testId }) => (
  <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4" data-testid={testId}>
    <Skeleton className="h-6 w-3/4" />
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-2/3" />
    <div className="flex gap-2">
      <Skeleton className="h-6 w-16 rounded-full" />
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
  </div>
);

export const SkeletonGrid: React.FC<{ count?: number }> = ({ count = 12 }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="skeleton-grid">
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonCard key={i} data-testid={`skeleton-card-${i}`} />
    ))}
  </div>
);

// Compass-specific skeleton components
export const CompassSkeleton: React.FC = () => (
  <div className="space-y-8" data-testid="compass-skeleton">
    {/* Header skeleton */}
    <div className="space-y-4" data-testid="compass-header-skeleton">
      <Skeleton className="h-8 w-1/3" data-testid="compass-title-skeleton" />
      <Skeleton className="h-4 w-2/3" data-testid="compass-framing-skeleton" />
    </div>
    
    {/* Directions skeleton */}
    <div className="space-y-6" data-testid="compass-directions-skeleton">
      <Skeleton className="h-6 w-1/4" data-testid="compass-directions-title-skeleton" />
      <div className="grid gap-6 md:grid-cols-2">
        {[1, 2].map((i) => (
          <div key={i} className="p-6 bg-white rounded-xl border border-gray-200 animate-pulse" data-testid={`compass-direction-skeleton-${i}`}>
            <Skeleton className="h-6 w-3/4 mb-3" />
            <Skeleton className="h-4 w-full mb-4" />
            <Skeleton className="h-10 w-full" />
          </div>
        ))}
      </div>
    </div>
    
    {/* Conversation skeleton */}
    <div className="space-y-6" data-testid="compass-conversation-skeleton">
      <Skeleton className="h-6 w-1/4" data-testid="compass-conversation-title-skeleton" />
      <div className="p-6 bg-white rounded-xl border border-gray-200 space-y-4">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    </div>
  </div>
);

export const DirectionCardSkeleton: React.FC = () => (
  <div className="p-6 bg-white rounded-xl border border-gray-200 animate-pulse" data-testid="direction-card-skeleton">
    <Skeleton className="h-6 w-3/4 mb-3" data-testid="direction-title-skeleton" />
    <Skeleton className="h-4 w-full mb-4" data-testid="direction-description-skeleton" />
    <Skeleton className="h-10 w-full" data-testid="direction-button-skeleton" />
  </div>
);

export const ConversationSkeleton: React.FC = () => (
  <div className="space-y-6" data-testid="conversation-skeleton">
    <Skeleton className="h-6 w-1/4" data-testid="conversation-title-skeleton" />
    <div className="p-6 bg-white rounded-xl border border-gray-200 space-y-4" data-testid="conversation-composer-skeleton">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
    <div className="space-y-4" data-testid="conversation-list-skeleton">
      {[1, 2, 3].map((i) => (
        <div key={i} className="p-4 bg-white rounded-lg border border-gray-200 animate-pulse" data-testid={`conversation-item-skeleton-${i}`}>
          <div className="flex items-center gap-2 mb-2">
            <Skeleton className="w-6 h-6 rounded-full" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        </div>
      ))}
    </div>
  </div>
);
