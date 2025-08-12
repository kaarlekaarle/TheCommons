import React from 'react';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';
import type { PrincipleItem, ActionItem } from '../../types/content';

interface ContentListProps {
  title: string;
  items: (PrincipleItem | ActionItem)[];
  loading?: boolean;
  error?: string | null;
  compact?: boolean;
  emptyMessage?: string;
  className?: string;
}

export default function ContentList({
  title,
  items,
  loading = false,
  error = null,
  compact = false,
  emptyMessage = "No items available",
  className = ""
}: ContentListProps) {
  if (loading) {
    return (
      <div className={`gov-card ${className}`}>
        <h3 className="gov-card-title">{title}</h3>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gov-text-muted rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gov-text-muted rounded w-full mb-1"></div>
              <div className="h-3 bg-gov-text-muted rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`gov-card ${className}`}>
        <h3 className="gov-card-title">{title}</h3>
        <div className="flex items-center space-x-2 text-gov-text-muted">
          <AlertCircle className="w-4 h-4" />
          <span>Unable to load content</span>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className={`gov-card ${className}`}>
        <h3 className="gov-card-title">{title}</h3>
        <div className="flex items-center space-x-2 text-gov-text-muted">
          <Clock className="w-4 h-4" />
          <span>{emptyMessage}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`gov-card ${className}`}>
      <h3 className="gov-card-title">{title}</h3>
      <div className="space-y-4">
        {items.map((item) => (
          <div
            key={item.id}
            className={`border-l-4 border-gov-primary pl-4 ${
              compact ? 'py-2' : 'py-3'
            }`}
          >
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-gov-primary mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <h4 className={`font-semibold text-white ${
                  compact ? 'text-sm' : 'text-base'
                }`}>
                  {item.title}
                </h4>
                <p className={`text-gov-text-muted mt-1 ${
                  compact ? 'text-sm' : 'text-base'
                }`}>
                  {item.description}
                </p>
                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {item.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-block px-2 py-1 text-xs bg-gov-secondary text-white rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
                {!compact && item.source && (
                  <p className="text-xs text-gov-text-muted mt-2">
                    Source: {item.source}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
