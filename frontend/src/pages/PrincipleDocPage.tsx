import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Share2, Calendar, Tag } from 'lucide-react';
import { getPoll, listComments, createComment, getResults, getPollOptions } from '../lib/api';
import { useToast } from '../components/ui/useToast';
import Button from '../components/ui/Button';
import { principlesCopy } from '../copy/principles';
import { flags } from '../config/flags';
import PerspectiveCard from '../components/principle/PerspectiveCard';
import ConversationSection from '../components/principle/ConversationSection';
import FurtherLearning from '../components/principle/FurtherLearning';
import { computePrimaryOption, isTie } from '../utils/perspective';
import type { Poll, Comment, PollResults, PollOption } from '../types';

type SectionState = 'idle' | 'loading' | 'ready' | 'error';

export default function PrincipleDocPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { success, error: showError } = useToast();

  // State
  const [poll, setPoll] = useState<Poll | null>(null);
  const [pollOptions, setPollOptions] = useState<PollOption[]>([]);
  const [results, setResults] = useState<PollResults | null>(null);
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

  const fetchPollOptions = useCallback(async () => {
    if (!id) return;

    setOptionsState('loading');
    try {
      const optionsData = await getPollOptions(id);
      setPollOptions(optionsData);
      setOptionsState('ready');
    } catch (err) {
      console.error('Failed to fetch poll options:', err);
      setOptionsState('error');
    }
  }, [id]);

  const fetchResults = useCallback(async () => {
    if (!id) return;

    setResultsState('loading');
    try {
      const resultsData = await getResults(id);
      setResults(resultsData);
      setResultsState('ready');
    } catch (err) {
      console.error('Failed to fetch results:', err);
      setResultsState('error');
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
      fetchPollOptions();
      fetchResults();
      fetchComments();
    }
  }, [id]);

  // Compute primary perspective based on results
  const primaryOption = pollOptions.length > 0 && results ? computePrimaryOption(pollOptions, results) : null;
  const isTieResult = primaryOption ? isTie(primaryOption) : true;

  // Compute percentages and trend data
  const primaryPercent = results && primaryOption ?
    Math.round((results.options.find(r => r.option_id === primaryOption.primaryId)?.percentage || 0)) : null;
  const alternatePercent = results && primaryOption ?
    Math.round((results.options.find(r => r.option_id === primaryOption.alternateId)?.percentage || 0)) : null;

  // Mock trend data (in real implementation, this would come from historical data)
  const primaryTrend7d = primaryPercent ? Math.floor(Math.random() * 7) - 3 : null; // Random -3 to +3 for demo

  // Analytics tracking for primary perspective shown
  useEffect(() => {
    if (primaryOption && !isTieResult && flags.primaryPerspectiveEnabled) {
      const primaryShare = results?.optionResults?.[primaryOption.primaryId]?.votes || 0;
      const totalVotes = results?.totalVotes || 1;
      const share = primaryShare / totalVotes;

      console.log('perspective.primary_shown', {
        primaryId: primaryOption.primaryId,
        share: Math.round(share * 100)
      });
    }
  }, [primaryOption, isTieResult, results]);

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
    <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
      <div className="space-y-8">
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
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 xl:grid-cols-3">
          {/* Main Content Column (span 2) */}
          <section className="lg:col-span-2 space-y-6">
            {/* Primary Perspective - Full Width, Prominent */}
            <div className="w-full">
              {flags.primaryPerspectiveEnabled && primaryOption && !isTieResult ? (
                // Dynamic primary perspective layout - Hierarchical
                <>
                  {/* Primary Perspective (majority) - Full Width, Prominent */}
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
                    showBadge={true}
                    badgeText={principlesCopy.primaryPerspective.badge}
                    isPrimary={true}
                    trend7d={primaryTrend7d}
                  />

                  {/* Alternate Perspective (minority) - Below, Smaller */}
                  <div className="mt-6">
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
                      showBadge={false}
                      isPrimary={false}
                      isSecondary={true}
                    />
                  </div>
                </>
              ) : (
                // Equal weight layout (tie or feature flag off) - Side by side
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
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
                    showBadge={false}
                    isPrimary={false}
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
                    showBadge={false}
                    isPrimary={false}
                  />
                </div>
              )}
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
          </section>

          {/* Sidebar (right column) */}
          <aside className="lg:col-span-1" role="complementary">
            <div className="lg:sticky lg:top-20 space-y-6">
              <FurtherLearning />

              {/* Meta Card */}
              <div className="bg-white rounded-2xl border border-gray-200/60 shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Meta</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">{principlesCopy.meta.lastUpdated}:</span>
                    <span className="text-gray-900">
                      {poll?.updated_at ? new Date(poll.updated_at).toLocaleDateString() : 'Unknown'}
                    </span>
                  </div>
                  {primaryPercent !== null && alternatePercent !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">{principlesCopy.meta.currentLeaning}:</span>
                      <span className="text-gray-900">
                        Primary {primaryPercent}% • Alternate {alternatePercent}%
                      </span>
                    </div>
                  )}
                  {primaryTrend7d !== null && primaryTrend7d !== 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">{principlesCopy.meta.change7Days}:</span>
                      <span className="text-gray-900">
                        {primaryTrend7d > 0 ? '+' : ''}{primaryTrend7d}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}
