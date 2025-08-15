import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Share2, Calendar, Tag } from 'lucide-react';
import { getPoll, listComments, createComment } from '../lib/api';
import { useToast } from '../components/ui/useToast';
import Button from '../components/ui/Button';
import { principlesCopy } from '../copy/principles';
import { flags } from '../config/flags';
import PerspectiveCard from '../components/principle/PerspectiveCard';
import ConversationSection from '../components/principle/ConversationSection';
import FurtherLearning from '../components/principle/FurtherLearning';
import type { Poll, Comment } from '../types';

type SectionState = 'idle' | 'loading' | 'ready' | 'error';

export default function PrincipleDocPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { success, error: showError } = useToast();

  // State
  const [poll, setPoll] = useState<Poll | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAligning, setIsAligning] = useState(false);
  const [userAlignment, setUserAlignment] = useState<'primary' | 'alternate' | null>(null);
  const [expandedPerspective, setExpandedPerspective] = useState<'primary' | 'alternate' | null>(
    searchParams.get('p') as 'primary' | 'alternate' | null
  );

  // Section states
  const [pollState, setPollState] = useState<SectionState>('idle');
  const [commentsState, setCommentsState] = useState<SectionState>('idle');

  // Fetch data
  const fetchPoll = useCallback(async () => {
    if (!id) return;

    setPollState('loading');
    try {
      const pollData = await getPoll(id);
      setPoll(pollData);
      setPollState('ready');
    } catch (err) {
      console.error('Failed to fetch poll:', err);
      setPollState('error');
      showError('Failed to load principle');
    }
  }, [id]);

  const fetchComments = useCallback(async () => {
    if (!id) return;

    setCommentsState('loading');
    try {
      const commentsData = await listComments(id);
      setComments(commentsData.comments);
      setCommentsState('ready');
    } catch (err) {
      console.error('Failed to fetch comments:', err);
      setCommentsState('error');
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      fetchPoll();
      fetchComments();
    }
  }, [id]);

  // Handle conversation submission
  const handleConversationSubmit = async (body: string, perspective: 'primary' | 'alternate') => {
    if (!id) return;

    setIsSubmitting(true);
    try {
      const newComment = await createComment(id, {
        body,
        perspective // This will be mapped to the appropriate API field
      });

      // Optimistic update
      setComments(prev => [newComment, ...prev]);
      success('Reasoning posted successfully');

      // Analytics tracking
      console.log('principle.conversation.post', { pollId: id, perspective });
    } catch (err) {
      console.error('Failed to post reasoning:', err);
      showError('Failed to post reasoning');

      // Analytics tracking
      console.log('principle.conversation.error', { pollId: id, error: err });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle alignment
  const handleAlign = async (perspective: 'primary' | 'alternate') => {
    if (!id) return;

    setIsAligning(true);
    try {
      // This would typically call an API to update user alignment
      // For now, we'll just update local state
      setUserAlignment(perspective);
      success(`You're now aligned with the ${perspective} perspective`);

      // Analytics tracking
      console.log('principle.align', { pollId: id, perspective });
    } catch (err) {
      console.error('Failed to align:', err);
      showError('Failed to update alignment');
    } finally {
      setIsAligning(false);
    }
  };

  const handleBack = () => {
    navigate('/proposals');
  };

  if (pollState === 'error') {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-red-600 mb-4">{principlesCopy.error}</p>
          <Button onClick={fetchPoll}>{principlesCopy.retry}</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="text-gray-700 hover:text-gray-900"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Proposals
            </Button>
          </div>

          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2" data-testid="main-question">
                {principlesCopy.mainQuestion}
              </h1>
              <p className="text-gray-600 mb-2" data-testid="intro-text">
                {principlesCopy.introText}
              </p>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>{principlesCopy.lastUpdated}: {poll?.updated_at ? new Date(poll.updated_at).toLocaleDateString() : 'Unknown'}</span>
                </div>
                {poll?.labels && poll.labels.length > 0 && (
                  <div className="flex items-center gap-1">
                    <Tag className="w-4 h-4" />
                    <span>{principlesCopy.labels}: {poll.labels.map(l => l.name).join(', ')}</span>
                  </div>
                )}
              </div>
            </div>
            <Button variant="secondary" size="sm">
              <Share2 className="w-4 h-4 mr-2" />
              {principlesCopy.share}
            </Button>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Main Column */}
          <div className="lg:col-span-8 space-y-6">
            {/* Perspective Cards */}
            <div className="grid gap-6 md:grid-cols-2">
              <PerspectiveCard
                type="primary"
                title={principlesCopy.primaryPerspective.title}
                summary={principlesCopy.primaryPerspective.summary}
                longBody={principlesCopy.primaryPerspective.longBody}
                isAligned={userAlignment === 'primary'}
                isSubmitting={isAligning}
                onAlign={() => handleAlign('primary')}
                onToggleExpanded={() => setExpandedPerspective(expandedPerspective === 'primary' ? null : 'primary')}
                isExpanded={expandedPerspective === 'primary'}
                readMoreText={principlesCopy.primaryPerspective.readMore}
                readLessText={principlesCopy.primaryPerspective.readLess}
                alignButtonText={principlesCopy.primaryPerspective.alignButton}
              />

              <PerspectiveCard
                type="alternate"
                title={principlesCopy.alternatePerspective.title}
                summary={principlesCopy.alternatePerspective.summary}
                longBody={principlesCopy.alternatePerspective.longBody}
                isAligned={userAlignment === 'alternate'}
                isSubmitting={isAligning}
                onAlign={() => handleAlign('alternate')}
                onToggleExpanded={() => setExpandedPerspective(expandedPerspective === 'alternate' ? null : 'alternate')}
                isExpanded={expandedPerspective === 'alternate'}
                readMoreText={principlesCopy.alternatePerspective.readMore}
                readLessText={principlesCopy.alternatePerspective.readLess}
                alignButtonText={principlesCopy.alternatePerspective.alignButton}
              />
            </div>

            {/* Conversation Section */}
            <ConversationSection
              comments={comments}
              onSubmit={handleConversationSubmit}
              isSubmitting={isSubmitting}
              loading={commentsState === 'loading'}
              error={commentsState === 'error' ? 'Failed to load conversation' : null}
              onRetry={fetchComments}
            />
          </div>

          {/* Aside Column */}
          <div className="lg:col-span-4 space-y-6">
            <FurtherLearning />

            {/* Meta Card */}
            <div className="bg-white rounded-2xl border border-gray-200/60 shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Meta</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">{principlesCopy.created}:</span>
                  <span className="text-gray-900">
                    {poll?.created_at ? new Date(poll.created_at).toLocaleDateString() : 'Unknown'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">{principlesCopy.updated}:</span>
                  <span className="text-gray-900">
                    {poll?.updated_at ? new Date(poll.updated_at).toLocaleDateString() : 'Unknown'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">{principlesCopy.labels}:</span>
                  <span className="text-gray-900">
                    {poll?.labels && poll.labels.length > 0
                      ? poll.labels.map(l => l.name).join(', ')
                      : principlesCopy.noLabels
                    }
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
