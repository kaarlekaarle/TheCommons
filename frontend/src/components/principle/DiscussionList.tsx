import React from 'react';
import Card from '../ui/Card';
import { principlesCopy } from '../../copy/principles';
import type { Comment } from '../../types';

interface DiscussionListProps {
  comments: Comment[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export default function DiscussionList({
  comments,
  loading = false,
  error = null,
  onRetry
}: DiscussionListProps) {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-32 bg-gray-200 rounded"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="border-b border-gray-200 pb-4 space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-24"></div>
                  <div className="h-4 bg-gray-200 rounded w-20"></div>
                </div>
                <div className="space-y-1">
                  <div className="h-4 bg-gray-200 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              {principlesCopy.retry}
            </button>
          )}
        </div>
      </Card>
    );
  }

  // Filter out revision comments for discussion view
  const discussionComments = comments.filter(comment => comment.kind !== 'revision');

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {principlesCopy.subviews.discussion}
      </h3>

      {discussionComments.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-600">No discussion yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {discussionComments.map((comment) => (
            <div
              key={comment.id}
              className="border-b border-gray-200 pb-4 last:border-b-0"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-sm font-medium">
                  {(comment.user?.name || 'A')[0].toUpperCase()}
                </div>
                <span className="font-medium text-gray-900">
                  {comment.user?.name || 'Anonymous'}
                </span>
                <span className="text-gray-500">•</span>
                <span className="text-gray-500 text-sm">
                  {new Date(comment.created_at).toLocaleDateString()}
                </span>
              </div>

              <div className="text-gray-700 leading-relaxed ml-10">
                {comment.body}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
