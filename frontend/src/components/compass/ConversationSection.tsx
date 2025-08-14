import { useState, useEffect, useCallback, useRef } from 'react';
import { MessageCircle, Send, Clock, User } from 'lucide-react';
import { listComments, createComment } from '../../lib/api';
import { compassCopy } from '../../copy/compass';
import { compassAnalytics } from '../../lib/analytics';
import type { Comment } from '../../types';
import type { Direction } from './DirectionCards';
import Button from '../ui/Button';
import { useToast } from '../ui/useToast';
import { ConversationSkeleton } from '../ui/Skeleton';

type SectionStatus = 'idle' | 'loading' | 'ready' | 'empty' | 'error' | 'posting';

interface SectionState {
  status: SectionStatus;
  error?: string;
  retryCount: number;
}

type Props = {
  pollId: string;
  directions: Direction[];
  myAlignment: string | null;
  onStateChange?: (state: SectionState) => void;
  onRetry?: () => void;
};

export default function ConversationSection({ 
  pollId, 
  directions, 
  myAlignment, 
  onStateChange,
  onRetry 
}: Props) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newReasoning, setNewReasoning] = useState('');
  const [selectedDirectionId, setSelectedDirectionId] = useState<string | null>(myAlignment);
  const [sectionState, setSectionState] = useState<SectionState>({ status: 'idle', retryCount: 0 });
  
  const abortControllerRef = useRef<AbortController | null>(null);
  const { success, error: showError } = useToast();

  // Update parent state when local state changes
  useEffect(() => {
    onStateChange?.(sectionState);
  }, [sectionState, onStateChange]);

  const loadComments = useCallback(async (signal?: AbortSignal) => {
    // Cancel any existing requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    const requestSignal = signal || abortController.signal;
    
    try {
      setSectionState(prev => ({ ...prev, status: 'loading' }));
      
      const data = await listComments(pollId, { limit: 10 }, requestSignal);
      
      if (requestSignal.aborted) return;
      
      setComments(data.comments);
      setSectionState({ 
        status: data.comments.length > 0 ? 'ready' : 'empty', 
        retryCount: 0 
      });
    } catch (err: unknown) {
      if (requestSignal.aborted) return;
      
      const error = err as { message: string };
      console.error('Failed to load comments:', error);
      
      setSectionState(prev => ({ 
        status: 'error', 
        error: 'Could not load community reasoning.',
        retryCount: prev.retryCount 
      }));
      compassAnalytics.error('conversation', error.message || 'Failed to load comments');
    }
  }, [pollId]);

  useEffect(() => {
    loadComments();
    
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [loadComments]);

  useEffect(() => {
    setSelectedDirectionId(myAlignment);
  }, [myAlignment]);

  const handleRetry = useCallback(() => {
    if (onRetry) {
      onRetry();
    } else {
      loadComments();
    }
  }, [onRetry, loadComments]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newReasoning.trim() || sectionState.status === 'posting' || newReasoning.length < 240) return;

    const originalReasoning = newReasoning;
    setNewReasoning('');
    setSectionState(prev => ({ ...prev, status: 'posting' }));

    // Track analytics
    compassAnalytics.reasonSubmit(pollId, selectedDirectionId || undefined, originalReasoning.length);

    try {
      const input: { body: string; option_id?: string } = { body: originalReasoning.trim() };
      if (selectedDirectionId) {
        input.option_id = selectedDirectionId;
      }
      
      const comment = await createComment(pollId, input);
      
      // Add the new comment to the list
      setComments(prev => [comment, ...prev]);
      setSectionState(prev => ({ ...prev, status: 'ready' }));
      
      success(compassCopy.postSuccess);
      compassAnalytics.reasonSuccess(pollId, comment.id);
      
      // Focus the new comment for accessibility
      setTimeout(() => {
        const newCommentElement = document.querySelector(`[data-comment-id="${comment.id}"]`);
        if (newCommentElement instanceof HTMLElement) {
          newCommentElement.focus();
        }
      }, 100);
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to post reasoning:', error);
      // Restore the text if posting failed
      setNewReasoning(originalReasoning);
      setSectionState(prev => ({ ...prev, status: 'ready' }));
      showError('Failed to post reasoning');
      compassAnalytics.error('conversation', error.message || 'Failed to post reasoning');
    }
  };

  const characterCount = newReasoning.length;
  const isOverLimit = characterCount > 1000;
  const isUnderLimit = characterCount < 240;
  const canSubmit = characterCount >= 240 && characterCount <= 1000 && sectionState.status !== 'posting';

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const truncateText = (text: string, maxLength: number = 300) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  // Show loading skeleton
  if (sectionState.status === 'loading') {
    return (
      <section id="conversation">
        <ConversationSkeleton />
      </section>
    );
  }

  // Show error state
  if (sectionState.status === 'error') {
    return (
      <section id="conversation">
        <div className="flex items-center gap-3 mb-6">
          <MessageCircle className="w-5 h-5 text-gray-600" />
          <h2 className="text-xl font-semibold text-gray-900">{compassCopy.reasoningTitle}</h2>
        </div>
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-red-700 mb-2">{sectionState.error}</p>
          <Button onClick={handleRetry} variant="ghost" size="sm">
            {compassCopy.retry}
          </Button>
        </div>
      </section>
    );
  }

  return (
    <section id="conversation">
      <div className="flex items-center gap-3 mb-6">
        <MessageCircle className="w-5 h-5 text-gray-600" />
        <h2 className="text-xl font-semibold text-gray-900">{compassCopy.reasoningTitle}</h2>
      </div>

      {/* Composer */}
      <div className="p-6 bg-white rounded-xl border border-gray-200 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="reasoning-textarea" className="block text-sm font-medium text-gray-900 mb-2">
              {compassCopy.reasoningLabel}
            </label>
            <textarea
              id="reasoning-textarea"
              value={newReasoning}
              onChange={(e) => setNewReasoning(e.target.value)}
              placeholder="Share your thoughts on this direction and what future it enables..."
              className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-describedby="char-counter reasoning-helper"
              disabled={sectionState.status === 'posting'}
            />
            <div className="flex items-center justify-between mt-2">
              <span 
                id="reasoning-helper" 
                className="text-sm text-gray-600"
              >
                {compassCopy.reasoningHelper}
              </span>
              <span 
                id="char-counter" 
                className={`text-sm ${isOverLimit ? 'text-red-600' : isUnderLimit ? 'text-gray-500' : 'text-gray-700'}`}
                data-testid="char-counter"
              >
                {characterCount}/1000
              </span>
            </div>
          </div>

          {/* Direction selector */}
          {directions.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Which direction are you speaking for?
              </label>
              <div className="flex gap-2">
                {directions.map((direction) => (
                  <button
                    key={direction.id}
                    type="button"
                    onClick={() => setSelectedDirectionId(selectedDirectionId === direction.id ? null : direction.id)}
                    className={`px-3 py-1 text-sm rounded-full border ${
                      selectedDirectionId === direction.id
                        ? 'bg-blue-100 border-blue-300 text-blue-800'
                        : 'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100'
                    }`}
                    data-testid={`direction-selector-${direction.id}`}
                  >
                    {direction.title}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => setSelectedDirectionId(null)}
                  className={`px-3 py-1 text-sm rounded-full border ${
                    selectedDirectionId === null
                      ? 'bg-blue-100 border-blue-300 text-blue-800'
                      : 'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  No stance
                </button>
              </div>
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            disabled={!canSubmit}
            className="w-full"
            data-testid="submit-reasoning"
          >
            {sectionState.status === 'posting' ? (
              <>
                <Send className="w-4 h-4 mr-2 animate-spin" />
                {compassCopy.posting}
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                {compassCopy.postReasoning}
              </>
            )}
          </Button>
        </form>
      </div>

      {/* Comments list */}
      <div className="space-y-4">
        {sectionState.status === 'empty' ? (
          <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
            <p className="text-gray-700">{compassCopy.conversationEmpty}</p>
          </div>
        ) : (
          comments.map((comment) => (
            <div
              key={comment.id}
              className="p-4 bg-white rounded-lg border border-gray-200"
              data-comment-id={comment.id}
              tabIndex={-1}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center">
                  <User className="w-3 h-3 text-gray-600" />
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {comment.user?.name || 'Anonymous'}
                </span>
                <span className="text-sm text-gray-500">
                  <Clock className="w-3 h-3 inline mr-1" />
                  {formatDate(comment.created_at)}
                </span>
              </div>
              <div className="text-gray-700 leading-relaxed">
                {truncateText(comment.body)}
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
