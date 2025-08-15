import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Share2, Calendar, Tag } from 'lucide-react';
import { getPoll, listComments, createComment } from '../lib/api';
import { useToast } from '../components/ui/useToast';
import Button from '../components/ui/Button';
import { principlesCopy } from '../copy/principles';
import { flags } from '../config/flags';
import CommunityDocument from '../components/principle/CommunityDocument';
import CounterDocument from '../components/principle/CounterDocument';
import RevisionComposer from '../components/principle/RevisionComposer';
import RevisionsList from '../components/principle/RevisionsList';
import DiscussionList from '../components/principle/DiscussionList';
import AboutThis from '../components/principle/AboutThis';
import TabSwitcher from '../components/principle/TabSwitcher';
import type { Poll, Comment } from '../types';

interface EvidenceItem {
  id: string;
  title: string;
  source: string;
  year: number;
  url: string;
  summary?: string;
  stance?: 'supports' | 'questions' | 'mixed';
}

type SectionState = 'idle' | 'loading' | 'ready' | 'error';

export default function PrincipleDocPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { success, error: showError } = useToast();

  // State
  const [poll, setPoll] = useState<Poll | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [composerTarget, setComposerTarget] = useState<'main' | 'counter' | 'neutral'>('main');
  const [composerPlaceholder, setComposerPlaceholder] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'revisions' | 'discussion'>('revisions');

  // Section states
  const [pollState, setPollState] = useState<SectionState>('idle');
  const [commentsState, setCommentsState] = useState<SectionState>('idle');

  // Derived data
  const mainDoc = poll?.longform_main || poll?.description || poll?.body || '';
  const counterDoc = poll?.extra?.counter_body || '';
  const evidence: EvidenceItem[] = (poll?.extra?.evidence || []).map((item, index) => ({
    id: `evidence-${index}`,
    title: item.title,
    source: item.source,
    year: item.year,
    url: item.url,
    summary: (item as any).summary,
    stance: (item as any).stance
  }));

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

  // Handle revision submission
  const handleRevisionSubmit = async (body: string, target: 'main' | 'counter' | 'neutral') => {
    if (!id) return;

    setIsSubmitting(true);
    try {
      const newComment = await createComment(id, {
        body,
        kind: 'revision',
        stance: target
      });

      // Optimistic update
      setComments(prev => [newComment, ...prev]);
      success(principlesCopy.revisionPosted);

      // Analytics tracking
      console.log('principle.revision.post', { pollId: id, target });
    } catch (err) {
      console.error('Failed to post revision:', err);
      showError(principlesCopy.revisionError);

      // Analytics tracking
      console.log('principle.revision.error', { pollId: id, error: err });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle composer focus
  const handleDevelopView = () => {
    setComposerTarget('counter');
    setComposerPlaceholder('Develop the counter-document by proposing an alternative perspective...');
    // Focus management would go here
  };

  const handleSuggestSource = () => {
    setComposerTarget('neutral');
    setComposerPlaceholder('Suggest a source: [Title] - [Source], [Year] - [URL]');
    // Focus management would go here
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
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                {poll?.title || 'Loading...'}
              </h1>
              <p className="text-gray-600 mb-2">
                {poll?.description || 'Loading description...'}
              </p>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>{principlesCopy.lastUpdated}: {poll?.updated_at ? new Date(poll.updated_at).toLocaleDateString() : 'Unknown'}</span>
                </div>
                {flags.principlesDocEnabled && (
                  <button
                    onClick={() => navigate(`/compass/${id}/diff`)}
                    className="text-blue-600 hover:text-blue-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/60 focus:ring-offset-2 rounded"
                  >
                    Diff view
                  </button>
                )}
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
            <CommunityDocument
              content={mainDoc}
              loading={pollState === 'loading'}
            />

            <RevisionComposer
              onSubmit={handleRevisionSubmit}
              isSubmitting={isSubmitting}
              initialTarget={composerTarget}
              placeholder={composerPlaceholder}
            />

            {/* Tab Switcher */}
            <div>
              <TabSwitcher
                activeTab={activeTab}
                onTabChange={setActiveTab}
              />

              {/* Tab Content */}
              <div className="mt-4">
                {activeTab === 'revisions' ? (
                  <RevisionsList
                    revisions={comments}
                    loading={commentsState === 'loading'}
                    error={commentsState === 'error' ? 'Failed to load revisions' : null}
                    onRetry={fetchComments}
                  />
                ) : (
                  <DiscussionList
                    comments={comments}
                    loading={commentsState === 'loading'}
                    error={commentsState === 'error' ? 'Failed to load discussion' : null}
                    onRetry={fetchComments}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Aside Column */}
          <div className="lg:col-span-4 space-y-6">
            <CounterDocument
              content={counterDoc}
              onDevelopView={handleDevelopView}
              loading={pollState === 'loading'}
            />

            <AboutThis
              sources={evidence}
              onSuggestSource={handleSuggestSource}
              loading={pollState === 'loading'}
            />

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
