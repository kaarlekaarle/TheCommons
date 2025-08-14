import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, Send, Trash2, ThumbsUp, ThumbsDown } from 'lucide-react';
import { listComments, createComment, deleteComment, setCommentReaction } from '../../lib/api';
import type { Comment } from '../../types';
import Button from '../ui/Button';
import Empty from '../ui/Empty';
import { useToast } from '../ui/useToast';
import { Skeleton } from '../ui/Skeleton';

interface CommentsPanelProps {
  proposalId: string;
}

export default function CommentsPanel({ proposalId }: CommentsPanelProps) {
  const [items, setItems] = useState<Comment[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [posting, setPosting] = useState(false);
  const [newComment, setNewComment] = useState('');
  const isFetchingRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);
  const { success, error: showError } = useToast();

  const load = useCallback(async () => {
    if (isFetchingRef.current) return;
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    isFetchingRef.current = true;
    setError(null);
    try {
      const data = await listComments(proposalId, { signal: ac.signal });
      setItems(data.comments);
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        setError('Could not load comments.');
      }
    } finally {
      if (!ac.signal.aborted) {
        setLoading(false);
        isFetchingRef.current = false;
      }
    }
  }, [proposalId]);

  useEffect(() => {
    setLoading(true);
    load();
    return () => abortRef.current?.abort();
  }, [load]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || posting) return;

    const optimisticComment: Comment = {
      id: `temp-${Date.now()}`,
      poll_id: proposalId,
      user: { id: 'temp', username: 'You' },
      body: newComment.trim(),
      created_at: new Date().toISOString(),
      up_count: 0,
      down_count: 0,
      my_reaction: null
    };

    // Optimistic update
    setItems(prev => prev ? [optimisticComment, ...prev] : [optimisticComment]);
    const originalComment = newComment;
    setNewComment('');

    try {
      setPosting(true);
      const comment = await createComment(proposalId, { body: originalComment.trim() });
      // Replace optimistic comment with real one
      setItems(prev => prev ? prev.map(c => c.id === optimisticComment.id ? comment : c) : [comment]);
      success('Comment posted successfully');
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to post comment:', error.message);
      // Rollback optimistic update
      setItems(prev => prev ? prev.filter(c => c.id !== optimisticComment.id) : null);
      setNewComment(originalComment);
      showError('Failed to post comment');
    } finally {
      setPosting(false);
    }
  }, [newComment, posting, proposalId, success, showError]);

  const handleDelete = useCallback(async (commentId: string) => {
    try {
      await deleteComment(commentId);
      setItems(prev => prev ? prev.filter(c => c.id !== commentId) : null);
      success('Comment deleted successfully');
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to delete comment:', error.message);
      showError('Failed to delete comment');
    }
  }, [success, showError]);

  const handleReaction = useCallback(async (commentId: string, type: 'up' | 'down') => {
    try {
      // Optimistic update
      setItems(prev => prev ? prev.map(comment => {
        if (comment.id === commentId) {
          const currentReaction = comment.my_reaction;
          let newUpCount = comment.up_count;
          let newDownCount = comment.down_count;
          let newMyReaction: 'up' | 'down' | null = null;

          if (currentReaction === type) {
            // Toggle off
            if (type === 'up') newUpCount--;
            else newDownCount--;
          } else {
            // Set new reaction
            if (currentReaction === 'up') newUpCount--;
            else if (currentReaction === 'down') newDownCount--;
            
            if (type === 'up') newUpCount++;
            else newDownCount++;
            newMyReaction = type;
          }

          return {
            ...comment,
            up_count: newUpCount,
            down_count: newDownCount,
            my_reaction: newMyReaction
          };
        }
        return comment;
      }) : null);

      // API call
      const response = await setCommentReaction(commentId, type);
      
      // Update with server response
      setItems(prev => prev ? prev.map(comment => {
        if (comment.id === commentId) {
          return {
            ...comment,
            up_count: response.up_count,
            down_count: response.down_count,
            my_reaction: response.my_reaction
          };
        }
        return comment;
      }) : null);
    } catch (err: unknown) {
      const error = err as { status: number; message: string };
      
      // Revert optimistic update
      load();
      
      if (error.status === 401) {
        showError('Login to react to comments');
      } else {
        showError('Failed to update reaction');
      }
    }
  }, [load, showError]);

  const characterCount = newComment.length;
  const isOverLimit = characterCount > 2000;
  const isNearLimit = characterCount > 1600;

  return (
    <div data-testid="comments-container" className="fade-in" data-ready={!loading}>
      <div className="p-6 bg-surface border border-border rounded-lg">
        <div className="flex items-center gap-3 mb-6">
          <MessageCircle className="w-5 h-5 text-primary" />
          <h2 className="text-gray-900 font-semibold text-lg md:text-xl leading-tight">Discussion</h2>
        </div>
        
        {/* Comment Form */}
        <form onSubmit={handleSubmit} className="space-y-3 mb-6">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Share your thoughts..."
            className={`w-full p-3 border rounded-lg resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors placeholder-gray-500 ${
              isOverLimit ? 'border-red-300' : isNearLimit ? 'border-yellow-300' : 'border-border'
            }`}
            rows={3}
            maxLength={2000}
            disabled={posting}
          />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`text-xs ${
                isOverLimit ? 'text-red-600' : isNearLimit ? 'text-yellow-600' : 'text-gray-600'
              }`}>
                {characterCount}/2000
              </span>
              {isOverLimit && (
                <span className="text-xs text-red-600">Character limit exceeded</span>
              )}
            </div>
            <Button
              type="submit"
              disabled={!newComment.trim() || posting || isOverLimit}
              loading={posting}
              className="bg-primary-600 hover:bg-primary-700 text-white"
            >
              {posting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Posting...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Post
                </>
              )}
            </Button>
          </div>
        </form>

        {/* Comments List */}
        <div className="min-h-[120px]">
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-4 bg-surface border border-border rounded-lg">
                  <div className="flex items-start gap-3">
                    <Skeleton className="w-8 h-8 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-3 w-full" />
                      <Skeleton className="h-3 w-3/4" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-600 mb-2" aria-live="polite">{error}</p>
              <Button onClick={load} variant="ghost">Try again</Button>
            </div>
          ) : items && items.length === 0 ? (
            <Empty
              icon={<MessageCircle className="w-8 h-8" />}
              title="No comments yet"
              subtitle="Be the first to share a thought."
            />
          ) : (
            <div className="space-y-4">
              <AnimatePresence>
                {items?.map((comment) => (
                  <motion.div
                    key={comment.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.18, ease: "easeOut" }}
                    className="p-4 bg-surface border border-border rounded-lg"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-gray-900">{comment.user.username}</span>
                          <time className="text-xs text-gray-600">
                            {new Date(comment.created_at).toLocaleString()}
                          </time>
                        </div>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{comment.body}</p>
                        
                        {/* Reaction Bar */}
                        <div className="flex items-center gap-2 mt-3">
                          <button
                            onClick={() => handleReaction(comment.id, 'up')}
                            className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                              comment.my_reaction === 'up'
                                ? 'text-primary bg-primary/10'
                                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                            }`}
                            title="Thumbs up"
                            aria-pressed={comment.my_reaction === 'up'}
                          >
                            <ThumbsUp className="w-3 h-3" />
                            <span>{comment.up_count}</span>
                          </button>
                          
                          <button
                            onClick={() => handleReaction(comment.id, 'down')}
                            className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                              comment.my_reaction === 'down'
                                ? 'text-primary bg-primary/10'
                                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                            }`}
                            title="Thumbs down"
                            aria-pressed={comment.my_reaction === 'down'}
                          >
                            <ThumbsDown className="w-3 h-3" />
                            <span>{comment.down_count}</span>
                          </button>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(comment.id)}
                        className="flex-shrink-0 text-gray-600 hover:text-red-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
