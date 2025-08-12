import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, Send, Trash2, ThumbsUp, ThumbsDown } from 'lucide-react';
import { listComments, createComment, deleteComment, setCommentReaction } from '../lib/api';
import type { Comment } from '../types';
import Button from './ui/Button';
import Empty from './ui/Empty';
import { useToast } from './ui/useToast';

interface ProposalCommentsProps {
  pollId: string;
}

export default function ProposalComments({ pollId }: ProposalCommentsProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [newComment, setNewComment] = useState('');
  const { success, error: showError } = useToast();

  const fetchComments = async () => {
    try {
      setLoading(true);
      const data = await listComments(pollId);
      setComments(data.comments);
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to load comments:', error.message);
      showError('Failed to load comments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [pollId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || posting) return;

    try {
      setPosting(true);
      const comment = await createComment(pollId, newComment.trim());
      setComments(prev => [comment, ...prev]);
      setNewComment('');
      success('Comment posted successfully');
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to post comment:', error.message);
      showError('Failed to post comment');
    } finally {
      setPosting(false);
    }
  };

  const handleDelete = async (commentId: string) => {
    try {
      await deleteComment(commentId);
      setComments(prev => prev.filter(c => c.id !== commentId));
      success('Comment deleted successfully');
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to delete comment:', error.message);
      showError('Failed to delete comment');
    }
  };

  const handleReaction = async (commentId: string, type: 'up' | 'down') => {
    try {
      // Optimistic update
      setComments(prev => prev.map(comment => {
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
      }));

      // API call
      const response = await setCommentReaction(commentId, type);
      
      // Update with server response
      setComments(prev => prev.map(comment => {
        if (comment.id === commentId) {
          return {
            ...comment,
            up_count: response.up_count,
            down_count: response.down_count,
            my_reaction: response.my_reaction
          };
        }
        return comment;
      }));
    } catch (err: unknown) {
      const error = err as { status: number; message: string };
      
      // Revert optimistic update
      fetchComments();
      
      if (error.status === 401) {
        showError('Login to react to comments');
      } else {
        showError('Failed to update reaction');
      }
    }
  };

  const characterCount = newComment.length;
  const isOverLimit = characterCount > 2000;
  const isNearLimit = characterCount > 1600;

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <MessageCircle className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-semibold text-white">Discussion</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <MessageCircle className="w-5 h-5 text-primary" />
        <h3 className="text-lg font-semibold text-white">Discussion</h3>
      </div>

      {/* Comment Form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="relative">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Share your thoughts..."
            className={`w-full p-3 border rounded-lg resize-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors ${
              isOverLimit ? 'border-red-300' : isNearLimit ? 'border-yellow-300' : 'border-border'
            }`}
            rows={3}
            maxLength={2000}
            disabled={posting}
          />
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <span className={`text-xs ${
                isOverLimit ? 'text-red-500' : isNearLimit ? 'text-yellow-600' : 'text-muted'
              }`}>
                {characterCount}/2000
              </span>
              {isOverLimit && (
                <span className="text-xs text-red-500">Character limit exceeded</span>
              )}
            </div>
            <Button
              type="submit"
              disabled={!newComment.trim() || posting || isOverLimit}
              loading={posting}
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
        </div>
      </form>

      {/* Comments List */}
      {comments.length === 0 ? (
        <Empty
          icon={<MessageCircle className="w-8 h-8" />}
          title="No comments yet"
          subtitle="Start the conversation."
        />
      ) : (
        <div className="space-y-4">
          <AnimatePresence>
            {comments.map((comment) => (
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
                      <span className="font-medium text-white">{comment.user.username}</span>
                      <time className="text-xs text-muted">
                        {new Date(comment.created_at).toLocaleString()}
                      </time>
                    </div>
                    <p className="text-sm text-muted whitespace-pre-wrap">{comment.body}</p>
                    
                    {/* Reaction Bar */}
                    <div className="flex items-center gap-2 mt-3">
                      <button
                        onClick={() => handleReaction(comment.id, 'up')}
                        className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                          comment.my_reaction === 'up'
                            ? 'text-primary bg-primary/10'
                            : 'text-muted hover:text-white hover:bg-surface'
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
                            : 'text-muted hover:text-white hover:bg-surface'
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
                    className="flex-shrink-0 text-muted hover:text-red-500"
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
  );
}
