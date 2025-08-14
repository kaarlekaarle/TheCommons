import { useState, useEffect, useCallback, useRef } from 'react';
import { MessageCircle, Send, Clock, User } from 'lucide-react';
import { listComments, createComment } from '../../lib/api';
import { compassCopy } from '../../copy/compass';
import { compassAnalytics } from '../../lib/analytics';
import type { Comment } from '../../types';
import type { Direction } from './DirectionCards';
import Button from '../ui/Button';
import Segmented from '../ui/Segmented';
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
  const [about, setAbout] = useState<'a'|'b'|'general'>(
    myAlignment ? (myAlignment === directions[0]?.id ? 'a' : 'b') : 'general'
  );
  const [tone, setTone] = useState<'support'|'concern'|'neutral'>(
    myAlignment ? 'support' : 'neutral'
  );
  const [sectionState, setSectionState] = useState<SectionState>({ status: 'idle', retryCount: 0 });

  const abortControllerRef = useRef<AbortController | null>(null);
  const { success, error: showError } = useToast();

  // Derived state
  const selectedOptionId =
    about === 'a' ? directions[0]?.id :
    about === 'b' ? directions[1]?.id :
    undefined;

  // Effects
  useEffect(() => {
    // Enforce neutral when general is selected
    if (about === 'general') setTone('neutral');
  }, [about]);

  useEffect(() => {
    // Update about and tone when myAlignment changes
    if (myAlignment) {
      const newAbout = myAlignment === directions[0]?.id ? 'a' : 'b';
      setAbout(newAbout);
      setTone('support');
    } else {
      setAbout('general');
      setTone('neutral');
    }
  }, [myAlignment, directions]);

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

    try {
      let finalBody = originalReasoning.trim();
      if (about !== 'general') {
        finalBody = (tone === 'support' ? '[support] ' :
                     tone === 'concern' ? '[concern] ' : '') + finalBody;
      }

      const input: { body: string; option_id?: string } = { body: finalBody };
      if (selectedOptionId) {
        input.option_id = selectedOptionId;
      }

      const comment = await createComment(pollId, input);

      // Track analytics
      compassAnalytics.reasoning_submitted({
        pollId,
        optionId: selectedOptionId ?? null,
        stance: tone,
        chars: finalBody.length
      });

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
  const needsOption = tone !== 'neutral' && !selectedOptionId;
  const canSubmit = characterCount >= 240 && characterCount <= 1000 && !needsOption && sectionState.status !== 'posting';

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

  const parseStance = (text: string) => {
    if (text.startsWith('[support]')) return { stance: 'support' as const, clean: text.replace('[support]', '').trim() };
    if (text.startsWith('[concern]')) return { stance: 'concern' as const, clean: text.replace('[concern]', '').trim() };
    return { stance: null, clean: text };
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
        <h2 className="text-xl font-semibold text-gray-900">{compassCopy.conversationHeader}</h2>
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
              placeholder={compassCopy.conversationPlaceholder}
              className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-describedby="char-counter reasoning-helper"
              disabled={sectionState.status === 'posting'}
            />
            <p className="mt-2 text-sm text-gray-600">{compassCopy.reasoningHelper}</p>
          </div>

          {/* About selector */}
          {directions.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                {compassCopy.aboutLabel}
              </label>
              <Segmented
                name="about"
                value={about}
                onChange={(v) => setAbout(v as 'a'|'b'|'general')}
                options={[
                  { value: 'a', label: directions[0]?.title ?? 'Direction A' },
                  { value: 'b', label: directions[1]?.title ?? 'Direction B' },
                  { value: 'general', label: compassCopy.aboutGeneral },
                ]}
              />
            </div>
          )}

          {/* Tone selector */}
          {about !== 'general' && (
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                {compassCopy.toneLabel}
              </label>
              <Segmented
                name="tone"
                value={tone}
                onChange={(v) => setTone(v as 'support'|'concern'|'neutral')}
                options={[
                  { value: 'support', label: compassCopy.toneSupport },
                  { value: 'concern', label: compassCopy.toneConcern },
                ]}
              />
              <div className="text-xs text-gray-600 mt-1" aria-live="polite">
                {tone === 'support' ? compassCopy.hintSupport : compassCopy.hintConcern}
              </div>
            </div>
          )}

          <div className="mt-4 flex items-center justify-between">
            <span className={`text-sm ${isOverLimit || isUnderLimit ? 'text-red-600' : 'text-gray-600'}`}>
              {characterCount}/1000
            </span>
            <Button
              type="submit"
              variant="primary"
              disabled={!canSubmit}
              data-testid="post-reasoning"
            >
              {sectionState.status === 'posting' ? (
                <>
                  <Send className="w-4 h-4 mr-2 animate-spin" />
                  {compassCopy.posting}
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  {about === 'general'
                    ? compassCopy.postReasoning
                    : tone === 'support'
                      ? `Post support for ${about === 'a' ? directions[0]?.title : directions[1]?.title}`
                      : `Post concern about ${about === 'a' ? directions[0]?.title : directions[1]?.title}`}
                </>
              )}
            </Button>
          </div>
        </form>
      </div>

      {/* Comments list */}
      <div className="space-y-4">
        {sectionState.status === 'empty' ? (
          <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
            <p className="text-gray-700">{compassCopy.conversationEmpty}</p>
          </div>
        ) : (
          comments.map((comment) => {
            const { stance, clean } = parseStance(comment.body);
            const respondingTo = comment.option_id ? directions.find(d => d.id === comment.option_id) : null;

            return (
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
                    {comment.user?.username || 'Anonymous'}
                  </span>
                  <span className="text-sm text-gray-500">
                    <Clock className="w-3 h-3 inline mr-1" />
                    {formatDate(comment.created_at)}
                  </span>
                </div>

                {/* Stance and direction info */}
                <div className="flex items-center gap-2 mb-2">
                  {stance && (
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      stance === 'support'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-orange-100 text-orange-800'
                    }`}>
                      {stance === 'support' ? compassCopy.stanceSupport : compassCopy.stanceConcern}
                    </span>
                  )}
                  {respondingTo && (
                    <span className="text-xs text-gray-600">
                      Responding to: {respondingTo.title}
                    </span>
                  )}
                </div>

                <div className="text-gray-700 leading-relaxed">
                  {truncateText(clean)}
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
