import React from 'react';
import Badge from '../ui/Badge';
import Card from '../ui/Card';
import { principlesCopy } from '../../copy/principles';
import type { Comment } from '../../types';

interface RevisionsListProps {
  revisions: Comment[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

type RevisionStatus = 'pending' | 'accepted' | 'declined' | 'merged';

interface RevisionItem {
  id: string;
  title: string;
  target: 'main' | 'counter' | 'neutral';
  status: RevisionStatus;
  timestamp: string;
  author: string;
  authorInitial: string;
}

export default function RevisionsList({
  revisions,
  loading = false,
  error = null,
  onRetry
}: RevisionsListProps) {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-32 bg-gray-200 rounded"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="border rounded-lg p-4 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="flex gap-2">
                  <div className="h-5 w-16 bg-gray-200 rounded"></div>
                  <div className="h-5 w-20 bg-gray-200 rounded"></div>
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

  // Convert comments to revision items
  const revisionItems: RevisionItem[] = revisions
    .filter(comment => comment.kind === 'revision')
    .map(comment => ({
      id: comment.id,
      title: comment.body.slice(0, 90) + (comment.body.length > 90 ? '...' : ''),
      target: comment.stance || 'neutral',
      status: 'pending' as RevisionStatus, // Mock status for now
      timestamp: new Date(comment.created_at).toLocaleDateString(),
      author: comment.user?.name || 'Anonymous',
      authorInitial: (comment.user?.name || 'A')[0].toUpperCase()
    }));

  const getStatusBadge = (status: RevisionStatus) => {
    const config = {
      pending: { label: 'Pending', className: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
      accepted: { label: 'Accepted', className: 'bg-green-100 text-green-800 border-green-200' },
      declined: { label: 'Declined', className: 'bg-red-100 text-red-800 border-red-200' },
      merged: { label: 'Merged', className: 'bg-blue-100 text-blue-800 border-blue-200' }
    };

    return (
      <Badge variant="outline" className={config[status].className}>
        {config[status].label}
      </Badge>
    );
  };

  const getTargetBadge = (target: string) => {
    const config = {
      main: { label: 'Community', className: 'bg-blue-50 text-blue-700 border-blue-200' },
      counter: { label: 'Counter', className: 'bg-purple-50 text-purple-700 border-purple-200' },
      neutral: { label: 'Neutral', className: 'bg-gray-50 text-gray-700 border-gray-200' }
    };

    return (
      <Badge variant="outline" className={config[target as keyof typeof config]?.className || config.neutral.className}>
        {config[target as keyof typeof config]?.label || 'Neutral'}
      </Badge>
    );
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {principlesCopy.subviews.revisions}
      </h3>

      {revisionItems.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-600">No revisions yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {revisionItems.map((revision) => (
            <div
              key={revision.id}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-medium text-gray-900 line-clamp-2">
                  {revision.title}
                </h4>
                <div className="flex items-center gap-2 ml-4">
                  {getStatusBadge(revision.status)}
                  {getTargetBadge(revision.target)}
                </div>
              </div>

              <div className="flex items-center justify-between text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-xs font-medium">
                    {revision.authorInitial}
                  </div>
                  <span>{revision.author}</span>
                  <span>•</span>
                  <span>{revision.timestamp}</span>
                </div>

                <button
                  className="text-blue-600 hover:text-blue-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                >
                  View thread
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
