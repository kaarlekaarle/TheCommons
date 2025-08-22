import { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, FileText, BarChart3, CheckCircle, XCircle, Minus, Compass, Target, Link as LinkIcon } from 'lucide-react';
import { getPoll, getPollOptions, getMyVoteForPoll, castVote, getResults } from '../lib/api';
import type { Poll, PollOption, Vote, PollResults, Label } from '../types';
import Button from '../components/ui/Button';
import CommentsPanel from '../components/comments/CommentsPanel';
import { useToast } from '../components/ui/useToast';

import LabelChip from '../components/ui/LabelChip';
import LinkedPrinciplesDrawer from '../components/LinkedPrinciplesDrawer';
import { flags } from '../config/flags';
import { useNavigate } from 'react-router-dom';
import PrincipleProposal from '../components/principle/PrincipleProposal';
import { getHardcodedPoll, getHardcodedPollOptions, isHardcodedPoll, getHardcodedVote } from '../utils/hardcodedData';

export default function ProposalDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [poll, setPoll] = useState<Poll | null>(null);
  const [options, setOptions] = useState<PollOption[]>([]);
  const [myVote, setMyVote] = useState<Vote | null>(null);
  const [results, setResults] = useState<PollResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState<string | null>(null);

  const [linkedDrawerOpen, setLinkedDrawerOpen] = useState(false);
  const [selectedLabel, setSelectedLabel] = useState<Label | null>(null);
  const { success, error: showError } = useToast();


  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional one-time fetch when id changes
  useEffect(() => {
    if (id) {
      fetchData();
    }
  }, [id]);

  // Handle deep-linking for linked principles drawer
  useEffect(() => {
    const linkedLabel = searchParams.get('linked');
    if (linkedLabel && poll && poll.labels) {
      const label = poll.labels.find(l => l.slug === linkedLabel);
      if (label) {
        setSelectedLabel(label);
        setLinkedDrawerOpen(true);
      }
    }
  }, [searchParams, poll]);

  const handleLabelClick = (label: Label) => {
    setSelectedLabel(label);
    setLinkedDrawerOpen(true);
    setSearchParams({ linked: label.slug });
  };

  const handleCloseDrawer = () => {
    setLinkedDrawerOpen(false);
    setSelectedLabel(null);
    setSearchParams({});
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      console.log('[DEBUG] Fetching proposal data for ID:', id);
      console.log('[DEBUG] Current token:', localStorage.getItem('token') ? 'Present' : 'Missing');

      // Check if this is a hardcoded poll ID
      if (id && isHardcodedPoll(id)) {
        console.log('[DEBUG] Using hardcoded data for poll:', id);

        const hardcodedPoll = getHardcodedPoll(id);
        const hardcodedOptions = getHardcodedPollOptions(id);
        const hardcodedVote = getHardcodedVote(id);

        if (hardcodedPoll) {
          setPoll(hardcodedPoll);
          setOptions(hardcodedOptions);
          setMyVote(hardcodedVote);

          // For hardcoded data, we don't have real results
          setResults(null);

          console.log('[DEBUG] Hardcoded proposal data loaded successfully');
          return;
        } else {
          console.log('[DEBUG] Hardcoded poll ID found but poll data missing, falling back to API');
        }
      }

      // Fetch core data (poll and options) first
      const [pollData, optionsData] = await Promise.all([
        getPoll(id!),
        getPollOptions(id!)
      ]);

      // Note: level_a proposals now use the new structured format within this component
      // No redirect needed - the PrincipleProposal component handles the display

      setPoll(pollData);
      setOptions(optionsData);

      // Fetch optional data (vote, results, and delegation) - these can fail without breaking the page
      try {
        const voteData = await getMyVoteForPoll(id!);
        setMyVote(voteData);
      } catch (voteError) {
        console.log('[DEBUG] Could not fetch vote data:', voteError);
        setMyVote(null);
      }

      try {
        const resultsData = await getResults(id!);
        setResults(resultsData);
      } catch (resultsError) {
        console.log('[DEBUG] Could not fetch results data:', resultsError);
        setResults(null);
      }



      console.log('[DEBUG] Proposal data loaded successfully');
    } catch (err: unknown) {
      const error = err as { message: string; status?: number };
      console.error('[DEBUG] Failed to load proposal:', error.message, 'Status:', error.status);

      // Check if it's an authentication error
      if (error.status === 401) {
        showError('Please log in to view this proposal');
        console.log('[DEBUG] Authentication error - token may be expired');
      } else if (error.status === 404) {
        showError('Proposal not found');
        console.log('[DEBUG] 404 error - proposal may not exist or be accessible');
      } else {
        showError('Failed to load proposal');
      }
    } finally {
      setLoading(false);
    }
  }, [id, showError]);

  const handleVote = async (optionId: string) => {
    if (!poll || voting) return;

    try {
      setVoting(optionId);

      // Check if this is a hardcoded poll
      if (isHardcodedPoll(poll.id)) {
        console.log('[DEBUG] Handling vote for hardcoded poll:', poll.id);
        const { createHardcodedVote } = await import('../utils/hardcodedData');
        const newVote = createHardcodedVote(poll.id, optionId);
        setMyVote(newVote);
        success('Vote cast successfully');
      } else {
        await castVote(poll.id, optionId);
        await fetchData(); // Refresh data
        success('Vote cast successfully');
      }
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to cast vote:', error.message);
      showError('Failed to cast vote');
    } finally {
      setVoting(null);
    }
  };

  const getVotePercentage = (optionId: string) => {
    if (!results) return 0;
    const option = results.options.find(o => o.option_id === optionId);
    return option ? option.percentage : 0;
  };

  const isVoted = !!myVote;
  const isClosed = false; // We'll handle this when status is available

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (!poll) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold mb-2">Proposal not found</h2>
          <Link to="/proposals">
            <Button variant="ghost">Back to Proposals</Button>
          </Link>
        </div>
      </div>
    );
  }

  // For level_a proposals, redirect to compass page if enabled
  if (poll.decision_type === 'level_a' && flags.compassEnabled) {
    navigate(`/compass/${id}`, { replace: true });
    return null;
  }

  // For level_a proposals, use the new structured format (fallback)
  if (poll.decision_type === 'level_a') {
    console.log('[DEBUG] Rendering level_a proposal with new layout for poll:', poll.id);
    const tally = results?.options.map(option => ({
      optionId: option.option_id,
      count: option.votes
    })) || [];

    return (
      <PrincipleProposal
        poll={poll}
        options={options}
        myVote={myVote}
        onVoteSubmit={handleVote}
        onChangeAlignmentTo={handleVote}
        isSubmitting={!!voting}
        onBack={() => navigate('/proposals')}
        tally={tally}
        totalVotes={results?.total_votes || 0}
      />
    );
  }

  // For level_b proposals, use the existing format
  return (
    <div className="container mx-auto px-4 pb-20 sm:pb-8">
      {/* Header */}
      <div className="mb-8">
        <Link to="/proposals" className="inline-flex items-center gap-2 text-body hover:text-strong transition-colors mb-4">
          <ArrowLeft className="w-4 h-4" />
          Back to Proposals
        </Link>
        <div className="flex items-center gap-3 mb-4">
          <h1 className="text-3xl font-bold text-strong">{poll.title}</h1>
          <span className={`px-3 py-1.5 text-xs font-medium rounded-full flex items-center gap-1 ${
            poll.decision_type === 'level_a'
              ? 'badge-level-a'
              : 'badge-level-b'
          }`}>
            {poll.decision_type === 'level_a' ? (
              <>
                <Compass className="w-3 h-3" />
                Principle
              </>
            ) : (
              <>
                <Target className="w-3 h-3" />
                Action
              </>
            )}
          </span>
        </div>

        {/* Labels */}
        {flags.labelsEnabled && poll.labels && poll.labels.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {poll.labels.map(label => (
              <LabelChip
                key={`detail-label-${label.id}`}
                label={label}
                size="sm"
                onClick={(slug) => {
                  // Navigate to topic page
                  window.location.href = `/t/${slug}`;
                }}
              />
            ))}
          </div>
        )}

        {/* Linked Principles Card - Only for actions */}
        {flags.labelsEnabled && poll.decision_type === 'level_b' && poll.labels && poll.labels.length > 0 && (
          <div className="banner-info rounded-lg mb-6">
            <div className="flex items-start gap-3">
              <LinkIcon className="w-5 h-5 text-blue-300 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-strong font-medium mb-2">Linked Principles</h3>
                        <p className="text-sm text-blue-700 mb-3">
          This action connects to these long-term principles:
        </p>
                <div className="flex flex-wrap gap-2">
                  {poll.labels.map(label => (
                    <button
                      key={`linked-principle-${label.id}`}
                      onClick={() => handleLabelClick(label)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-full bg-blue-500/20 text-blue-200 border border-blue-400/30 hover:bg-blue-500/30 hover:border-blue-400/50 transition-colors"
                    >
                      {label.name}
                      <span className="text-xs opacity-75">→ see related</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Level Context Banner */}
        <div className={`banner-info rounded-lg mb-6 ${
          poll.decision_type === 'level_a'
            ? ''
            : 'banner-ok'
        }`}>
          <div className="flex items-start gap-3">
            {poll.decision_type === 'level_a' ? (
              <Compass className="w-5 h-5 text-blue-300 mt-0.5 flex-shrink-0" />
            ) : (
              <Target className="w-5 h-5 text-emerald-300 mt-0.5 flex-shrink-0" />
            )}
            <div>
              <p className={`font-medium mb-1 text-strong`}>
                {poll.decision_type === 'level_a' ? 'Long-Term Direction' : 'Short-Term Action'}
              </p>
              <p className={`text-sm text-body`}>
                {poll.decision_type === 'level_a'
                  ? 'This principle sets the compass and guides all other decisions.'
                  : 'This action moves us forward now and can be adjusted as needed.'
                }
              </p>
            </div>
          </div>
        </div>

        <p className="text-body leading-relaxed mb-4">{poll.description}</p>
        {poll.decision_type === 'level_a' && poll.direction_choice && (
          <div className="banner-info rounded-lg mb-6">
            <div className="flex items-start gap-3">
              <Compass className="w-4 h-4 text-blue-300 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-strong font-medium text-sm mb-1">Direction Choice:</p>
                <p className="text-gray-900">{poll.direction_choice}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Details Section */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <FileText className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold text-strong">Details</h2>
            </div>
            <div className="p-6 bg-surface border border-border rounded-lg">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <span className="text-sm text-subtle">Created</span>
                  <p className="font-medium text-strong">{new Date(poll.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <span className="text-sm text-subtle">Updated</span>
                  <p className="font-medium text-strong">{new Date(poll.updated_at).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          </section>

          {/* Direction Section - Only show for principles */}
          {poll.decision_type === 'level_a' && poll.direction_choice && (
            <section>
              <div className="flex items-center gap-3 mb-6">
                <FileText className="w-5 h-5 text-blue-600" />
                <h2 className="text-xl font-semibold text-strong">Direction</h2>
              </div>
              <div className="p-6 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-strong font-medium">{poll.direction_choice}</p>
                <p className="text-sm text-body mt-2">
                  This baseline policy establishes the direction for future decisions in this area.
                </p>
              </div>
            </section>
          )}

          {/* Results Section - Only show if there are voting options */}
          {options.length > 0 && (
            <section>
              <div className="flex items-center gap-3 mb-6">
                <BarChart3 className="w-5 h-5 text-primary" />
                <h2 className="text-xl font-semibold text-strong">Results</h2>
              </div>
              <div className="p-6 bg-surface border border-border rounded-lg space-y-4">
                {results && results.total_votes > 0 ? (
                  options.map((option) => {
                    const percentage = getVotePercentage(option.id);
                    return (
                      <div key={option.id} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-strong">{option.text}</span>
                                                      <span className="text-sm text-subtle">{percentage.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-border rounded-full h-2 overflow-hidden">
                          <motion.div
                            className="h-full bg-primary rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${percentage}%` }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                          />
                        </div>
                                                  <div className="text-xs text-subtle">
                          {results.options.find(o => o.option_id === option.id)?.votes || 0} votes
                        </div>
                      </div>
                    );
                  })
                ) : (
                                      <p className="text-subtle text-center py-4">No votes yet</p>
                )}
              </div>
            </section>
          )}

          {/* Discussion Section */}
          <section>
            <CommentsPanel proposalId={poll.id} />
          </section>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-8">
            <div className="p-6 bg-surface border border-border rounded-lg space-y-4">
              <h3 className="font-semibold text-strong">Vote</h3>


              {isVoted ? (
                <div className="text-center py-4">
                  <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                  <p className="text-sm text-body">You've voted</p>
                </div>
              ) : options.length > 0 ? (
                <div className="space-y-3">
                  {options.map((option) => (
                    <Button
                      key={`desktop-option-${option.id}`}
                      onClick={() => handleVote(option.id)}
                      disabled={isClosed || voting === option.id}
                      loading={voting === option.id}
                      className="w-full justify-start"
                      variant={option.text.toLowerCase().includes('yes') || option.text.toLowerCase().includes('support') ? 'primary' : 'ghost'}
                    >
                      {option.text.toLowerCase().includes('yes') || option.text.toLowerCase().includes('support') && <CheckCircle className="w-4 h-4 mr-2" />}
                      {option.text.toLowerCase().includes('no') || option.text.toLowerCase().includes('reject') && <XCircle className="w-4 h-4 mr-2" />}
                      {option.text.toLowerCase().includes('abstain') || option.text.toLowerCase().includes('modify') && <Minus className="w-4 h-4 mr-2" />}
                      {option.text}
                    </Button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-sm text-body mb-2">No voting options available</p>
                  <p className="text-xs text-subtle">This proposal doesn't have voting options set up yet.</p>
                </div>
              )}
              {isClosed && (
                <div className="text-center py-2">
                  <span className="text-xs text-subtle bg-surface-muted px-2 py-1 rounded">Voting closed</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Sticky Action Bar */}
      {options.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-surface/95 backdrop-blur border-t border-border py-3 px-4 sm:hidden" style={{ paddingBottom: 'calc(0.75rem + env(safe-area-inset-bottom))' }}>
          <div className="flex gap-2">
            {isVoted ? (
              <div className="flex-1 text-center py-2">
                <CheckCircle className="w-5 h-5 text-green-500 mx-auto mb-1" />
                <p className="text-xs text-body">You've voted</p>
              </div>
            ) : (
              options.map((option) => (
                <Button
                  key={`mobile-option-${option.id}`}
                  onClick={() => handleVote(option.id)}
                  disabled={isClosed || voting === option.id}
                  loading={voting === option.id}
                  size="sm"
                  className="flex-1"
                  variant={option.text.toLowerCase().includes('yes') || option.text.toLowerCase().includes('support') ? 'primary' : 'ghost'}
                >
                  {option.text.toLowerCase().includes('yes') || option.text.toLowerCase().includes('support') && <CheckCircle className="w-4 h-4 mr-1" />}
                  {option.text.toLowerCase().includes('no') || option.text.toLowerCase().includes('reject') && <XCircle className="w-4 h-4 mr-1" />}
                  {option.text.toLowerCase().includes('abstain') || option.text.toLowerCase().includes('modify') && <Minus className="w-4 h-4 mr-1" />}
                  {option.text}
                </Button>
              ))
            )}
          </div>
        </div>
      )}



      {/* Linked Principles Drawer */}
      {selectedLabel && (
        <LinkedPrinciplesDrawer
          isOpen={linkedDrawerOpen}
          onClose={handleCloseDrawer}
          label={selectedLabel}
          currentPollId={poll?.id || ''}
        />
      )}
    </div>
  );
}
