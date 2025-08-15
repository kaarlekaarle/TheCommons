
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { principlesDocCopy } from '../../copy/principlesDoc';
import type { Comment } from '../../types';

interface ReasoningListProps {
  comments: Comment[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export default function ReasoningList({ comments, loading = false, error = null, onRetry }: ReasoningListProps) {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-4 bg-gray-200 rounded w-20"></div>
                  <div className="h-4 bg-gray-200 rounded w-24"></div>
                </div>
                <div className="h-4 bg-gray-200 rounded w-full"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
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
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {principlesDocCopy.reasoningTitle}
        </h3>
        <div className="text-center py-4">
          <p className="text-red-600 mb-4">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-blue-600 hover:text-blue-700 underline"
            >
              {principlesDocCopy.retry}
            </button>
          )}
        </div>
      </Card>
    );
  }

  const revisionComments = comments.filter(comment =>
    comment.kind === 'revision' || comment.body.includes('[revision]')
  );

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {principlesDocCopy.reasoningTitle}
      </h3>

      {revisionComments.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-600">
            No revision proposals yet. Be the first to suggest a change.
          </p>
        </div>
      ) : (
        <div className="space-y-4" aria-live="polite">
          {revisionComments.map((comment) => {
            const stance = comment.stance ||
              (comment.body.includes('[main]') ? 'main' :
               comment.body.includes('[counter]') ? 'counter' : 'neutral');

            const getStanceLabel = (stance: string) => {
              switch (stance) {
                case 'main': return principlesDocCopy.targetMain;
                case 'counter': return principlesDocCopy.targetCounter;
                case 'neutral': return principlesDocCopy.targetNeutral;
                default: return 'Unknown';
              }
            };

            const getStanceColor = (stance: string) => {
              switch (stance) {
                case 'main': return 'bg-blue-50 text-blue-700';
                case 'counter': return 'bg-orange-50 text-orange-700';
                case 'neutral': return 'bg-gray-50 text-gray-700';
                default: return 'bg-gray-50 text-gray-700';
              }
            };

            return (
              <div key={comment.id} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium text-gray-900">
                    {comment.user.username}
                  </span>
                  <Badge variant="default" className={getStanceColor(stance)}>
                    {getStanceLabel(stance)}
                  </Badge>
                  <time className="text-sm text-gray-600">
                    {new Date(comment.created_at).toLocaleDateString()}
                  </time>
                </div>
                <div className="text-gray-800 whitespace-pre-line">
                  {comment.body.replace(/\[(main|counter|neutral|revision)\]/g, '').trim()}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
