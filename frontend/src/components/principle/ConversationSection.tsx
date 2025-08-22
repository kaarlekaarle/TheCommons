import React, { useState } from 'react';
import { Send } from 'lucide-react';
import Button from '../ui/Button';
import TextArea from '../ui/TextArea';
import Badge from '../ui/Badge';
import { principlesCopy } from '../../copy/principles';
import type { Comment } from '../../types';

// Extended comment type with perspective/stance
interface ExtendedComment extends Comment {
  perspective?: 'primary' | 'alternate';
  stance?: 'primary' | 'alternate';
}

interface ConversationSectionProps {
  comments: Comment[];
  onSubmit: (body: string, perspective: 'primary' | 'alternate') => Promise<void>;
  isSubmitting: boolean;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export default function ConversationSection({
  comments,
  onSubmit,
  isSubmitting,
  loading,
  error,
  onRetry
}: ConversationSectionProps) {
  const [body, setBody] = useState('');
  const [perspective, setPerspective] = useState<'primary' | 'alternate'>('primary');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!body.trim() || isSubmitting) return;

    try {
      await onSubmit(body.trim(), perspective);
      setBody('');
      setPerspective('primary');
    } catch {
      // Error handling is done in the parent component
    }
  };

  const getPerspectiveLabel = (comment: Comment) => {
    // Map comment metadata to perspective label
    const extendedComment = comment as ExtendedComment;
    const commentPerspective = extendedComment.perspective || extendedComment.stance || 'primary';
    return commentPerspective === 'primary' ? 'Primary' : 'Alternate';
  };

  const getPerspectiveVariant = (comment: Comment) => {
    const extendedComment = comment as ExtendedComment;
    const commentPerspective = extendedComment.perspective || extendedComment.stance || 'primary';
    return commentPerspective === 'primary' ? 'default' : 'secondary';
  };

  return (
    <div className="space-y-6">
      {/* Composer */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4" data-testid="conversation-title">
          {principlesCopy.composer.title}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <TextArea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder={principlesCopy.composer.placeholder}
            rows={4}
            maxLength={1000}
            data-testid="conversation-textarea"
            required
            className="w-full"
          />

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" data-testid="perspective-label">
              {principlesCopy.composer.perspectiveLabel}
            </label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="perspective"
                  value="primary"
                  checked={perspective === 'primary'}
                  onChange={(e) => setPerspective(e.target.value as 'primary' | 'alternate')}
                  className="mr-2"
                  data-testid="perspective-primary-radio"
                />
                <span className="text-sm text-gray-700">
                  {principlesCopy.composer.perspectiveOptions.primary}
                </span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="perspective"
                  value="alternate"
                  checked={perspective === 'alternate'}
                  onChange={(e) => setPerspective(e.target.value as 'primary' | 'alternate')}
                  className="mr-2"
                  data-testid="perspective-alternate-radio"
                />
                <span className="text-sm text-gray-700">
                  {principlesCopy.composer.perspectiveOptions.alternate}
                </span>
              </label>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {principlesCopy.composer.helperText}
            </p>
            <Button
              type="submit"
              disabled={!body.trim() || isSubmitting}
              loading={isSubmitting}
              data-testid="conversation-submit"
            >
              <Send className="w-4 h-4 mr-2" />
              {principlesCopy.composer.submitButton}
            </Button>
          </div>
        </form>
      </div>

      {/* Comments List */}
      <div className="space-y-4">
        <h4 className="text-lg font-semibold text-gray-900">
          {principlesCopy.conversation.header}
        </h4>

        {loading && (
          <div className="text-center py-8">
            <p className="text-gray-500">Loading conversation...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={onRetry} variant="secondary">
              Try again
            </Button>
          </div>
        )}

        {!loading && !error && comments.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">Be the first to share your reasoning.</p>
          </div>
        )}

        {!loading && !error && comments.length > 0 && (
          <div className="space-y-4">
            {(comments ?? []).map((comment) => (
              <div
                key={comment.id}
                className="bg-white rounded-lg border border-gray-200 p-4"
                data-testid={`comment-${comment.id}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">
                      {comment.user?.username || 'Anonymous'}
                    </span>
                    <Badge variant={getPerspectiveVariant(comment)} size="sm">
                      {getPerspectiveLabel(comment)}
                    </Badge>
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(comment.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-gray-700 whitespace-pre-line">
                  {comment.body}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
