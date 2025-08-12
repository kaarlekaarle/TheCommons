import React from 'react';
import { TrendingUp, Clock, AlertCircle, ExternalLink } from 'lucide-react';
import type { StoryItem } from '../../types/content';

interface StoryCardsProps {
  stories: StoryItem[];
  loading?: boolean;
  error?: string | null;
  className?: string;
}

export default function StoryCards({
  stories,
  loading = false,
  error = null,
  className = ""
}: StoryCardsProps) {
  if (loading) {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="gov-card animate-pulse">
            <div className="h-4 bg-gov-text-muted rounded w-3/4 mb-3"></div>
            <div className="h-3 bg-gov-text-muted rounded w-full mb-2"></div>
            <div className="h-3 bg-gov-text-muted rounded w-2/3 mb-2"></div>
            <div className="h-3 bg-gov-text-muted rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className={`gov-card ${className}`}>
        <div className="flex items-center space-x-2 text-gov-text-muted">
          <AlertCircle className="w-4 h-4" />
          <span>Unable to load stories</span>
        </div>
      </div>
    );
  }

  if (stories.length === 0) {
    return (
      <div className={`gov-card ${className}`}>
        <div className="flex items-center space-x-2 text-gov-text-muted">
          <Clock className="w-4 h-4" />
          <span>No stories available</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}>
      {stories.map((story) => (
        <div key={story.id} className="gov-card hover:bg-gov-card-hover transition-colors">
          <div className="flex items-start space-x-3">
            <TrendingUp className="w-5 h-5 text-gov-primary mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-white text-base mb-2">
                {story.title}
              </h4>
              <p className="text-gov-text-muted text-sm mb-3">
                {story.summary}
              </p>
              {story.impact && (
                <div className="bg-gov-secondary/20 border border-gov-secondary/30 rounded p-3 mb-3">
                  <p className="text-gov-secondary text-sm font-medium">
                    Impact: {story.impact}
                  </p>
                </div>
              )}
              {story.link && (
                <a
                  href={story.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 text-gov-primary hover:text-gov-primary-light text-sm transition-colors"
                >
                  <span>Learn more</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
