import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Share2, Calendar, Clock } from 'lucide-react';
import { getPoll, getPollOptions, getMyVoteForPoll, castVote, getResults } from '../lib/api';
import { flags } from '../config/flags';
import { compassCopy, completeStreetsCopy as cc } from '../copy/compass';
import { compassAnalytics } from '../lib/analytics';
import type { Poll, PollOption, Vote } from '../types';
import Button from '../components/ui/Button';
import LabelChip from '../components/ui/LabelChip';
import { type Direction } from '../components/compass/DirectionCards';
import DirectionCard from '../components/compass/DirectionCard';
import { Expandable } from '../components/compass/Expandable';
import CompassTally from '../components/compass/CompassTally';
import ConversationSection from '../components/compass/ConversationSection';
import { CompassSkeleton } from '../components/ui/Skeleton';

// Helper to check for abort errors
const isAbortError = (err: unknown) =>
  err instanceof DOMException && err.name === 'AbortError';

// Debug logging (dev-only)
const dbg = (...args: unknown[]) => {
  if (import.meta?.env?.MODE === 'test') console.debug('[CompassPage]', ...args);
};

// Types
export type RetryScheduler = {
  wait(ms: number, signal?: AbortSignal): Promise<void>
};

export type SectionStatus = 'idle' | 'loading' | 'ready' | 'empty' | 'error' | 'posting';

export type SectionState = {
  status: SectionStatus;
  error?: string;
  retryCount: number;
};



// Default scheduler for production
const defaultScheduler: RetryScheduler = {
  wait: (ms, signal) =>
    new Promise((resolve, reject) => {
      const t = setTimeout(resolve, ms);
      signal?.addEventListener('abort', () => {
        clearTimeout(t);
        reject(new DOMException('Aborted', 'AbortError'));
      });
    })
};

// Backoff computation
const computeBackoff = (attempt: number) => Math.min(1000 * 2 ** (attempt - 1), 8000);

// Props
interface CompassPageProps {
  scheduler?: RetryScheduler;
}

export default function CompassPage({ scheduler = defaultScheduler }: CompassPageProps) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Core data
  const [poll, setPoll] = useState<Poll | null>(null);
  const [options, setOptions] = useState<PollOption[]>([]);
  const [_selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  void _selectedOptionId;
  const [myAlignment, setMyAlignment] = useState<string | null>(null);
  const [myVote, setMyVote] = useState<Vote | null>(null);
  const [tally, setTally] = useState<Array<{ optionId: string; count: number }>>([]);

  // Section state machines
  const [directionsState, setDirectionsState] = useState<SectionState>({ status: 'idle', retryCount: 0 });
  const [tallyState, setTallyState] = useState<SectionState>({ status: 'idle', retryCount: 0 });
  const [_conversationState, setConversationState] = useState<SectionState>({ status: 'idle', retryCount: 0 });
  void _conversationState;

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [voteError, setVoteError] = useState<string | null>(null);

  // Request cancellation
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastPollIdRef = useRef<string | null>(null);

  // Retry count tracking
  const retryCountRef = useRef<{ directions: number; tally: number; conversation: number }>({
    directions: 0,
    tally: 0,
    conversation: 0
  });

  // Analytics tracking
  useEffect(() => {
    if (poll && poll.id !== lastPollIdRef.current) {
      compassAnalytics.view(poll.id);
      lastPollIdRef.current = poll.id;
    }
  }, [poll]);

  // Main data fetching with proper cancellation
  const fetchCompass = useCallback(async (signal?: AbortSignal) => {
    if (!id) return;

    dbg('Starting fetchCompass for id:', id);

    // Use provided signal or abort controller signal
    const requestSignal = signal;

    if (!requestSignal) {
      dbg('No signal provided, cannot proceed');
      return;
    }

    try {
      // Reset section states to loading
      setDirectionsState({ status: 'loading', retryCount: 0 });
      setTallyState({ status: 'loading', retryCount: 0 });
      setConversationState({ status: 'loading', retryCount: 0 });

      dbg('Fetching poll and options...');

      // Fetch core data
      const [pollData, optionsData] = await Promise.all([
        getPoll(id, requestSignal),
        getPollOptions(id, requestSignal)
      ]);

      dbg('Poll and options fetched successfully:', { pollId: pollData.id, optionsCount: optionsData?.length });

      // Check if request was cancelled
      if (requestSignal.aborted) {
        dbg('Request aborted after poll/options fetch');
        return;
      }

      // Redirect if not a level_a poll
      if (pollData.decision_type !== 'level_a') {
        navigate(`/proposals/${id}`, { replace: true });
        return;
      }

      setPoll(pollData);

      // Handle options and set directions state to ready IMMEDIATELY
      if (optionsData && optionsData.length > 0) {
        setOptions(optionsData);
        setDirectionsState({ status: 'ready', retryCount: 0 });
        retryCountRef.current.directions = 0; // Reset retry count on success
        dbg('Directions ready with options:', optionsData.length);
      } else {
        setOptions([
          { id: 'placeholder-a', poll_id: pollData.id, text: 'Direction A', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
          { id: 'placeholder-b', poll_id: pollData.id, text: 'Direction B', created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
        ]);
        setDirectionsState({ status: 'ready', retryCount: 0 }); // Set to ready even with placeholder options
        retryCountRef.current.directions = 0; // Reset retry count on success
        dbg('Directions ready with placeholder options');
      }

      // Fetch user's current vote and results in parallel
      try {
        dbg('Fetching vote and results...');
        const [voteData, resultsData] = await Promise.all([
          getMyVoteForPoll(pollData.id, requestSignal),
          getResults(pollData.id, requestSignal)
        ]);

        // Check if request was cancelled
        if (requestSignal.aborted) {
          dbg('Request aborted after vote/results fetch');
          return;
        }

        // Handle vote data
        if (voteData) {
          setMyVote(voteData);
          setMyAlignment(voteData.option_id);
          setSelectedOptionId(voteData.option_id);
          dbg('Vote data loaded:', voteData.option_id);
        }

        // Handle results data and set tally state to ready
        if (resultsData && resultsData.options) {
          const tallyData = resultsData.options.map(option => ({
            optionId: option.option_id,
            count: option.votes
          }));
          setTally(tallyData);
          setTallyState({ status: 'ready', retryCount: 0 });
          retryCountRef.current.tally = 0; // Reset retry count on success
          dbg('Tally ready with results:', resultsData.options.length);
        } else {
          setTallyState({ status: 'ready', retryCount: 0 }); // Set to ready even with empty results
          retryCountRef.current.tally = 0; // Reset retry count on success
          dbg('Tally ready with empty results');
        }

      } catch (err) {
        if (isAbortError(err)) {
          dbg('Vote/results fetch aborted');
          return;
        }

        dbg('Could not fetch vote or results data:', err);
        // Set tally to ready even if vote/results fail (directions are the main content)
        setTallyState({ status: 'ready', retryCount: 0 });
        dbg('Tally set to ready despite vote/results error');
      }

    } catch (err: unknown) {
      if (isAbortError(err)) {
        dbg('Main fetch aborted');
        return;
      }

      const error = err as { message: string; status?: number };
      console.error('Failed to load compass:', error);
      dbg('Main fetch error:', error.message);

      // Set error state for directions (main section)
      setDirectionsState({
        status: 'error',
        error: error.message || 'Failed to load compass',
        retryCount: directionsState.retryCount
      });
      compassAnalytics.error('directions', error.message || 'Failed to load compass');
    }
  }, [id, navigate, directionsState.retryCount]);

  // Initialize fetch on mount and route change
  useEffect(() => {
    if (id) {
      dbg('useEffect triggered for id:', id);

      // Cancel any existing requests
      if (abortControllerRef.current) {
        dbg('Aborting existing request');
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      dbg('Created new AbortController');

      // Reset retry counts when ID changes
      retryCountRef.current = { directions: 0, tally: 0, conversation: 0 };

      // Fetch data
      fetchCompass(abortController.signal);
    }

    // Cleanup on unmount or route change
    return () => {
      if (abortControllerRef.current) {
        dbg('useEffect cleanup - aborting request');
        abortControllerRef.current.abort();
      }
    };
  }, [id, fetchCompass]); // Only depend on id to avoid infinite loops

  // Retry function with exponential backoff
  const retrySection = useCallback(async (section: 'directions' | 'tally' | 'conversation') => {
    const maxRetries = 3;

    // Get current retry count from ref
    const currentRetryCount = retryCountRef.current[section];

    if (currentRetryCount >= maxRetries) {
      return;
    }

    const newRetryCount = currentRetryCount + 1;
    retryCountRef.current[section] = newRetryCount;

    compassAnalytics.refetch(section, newRetryCount);

    // Update retry count in state
    if (section === 'directions') {
      setDirectionsState(prev => ({ ...prev, retryCount: newRetryCount }));
    } else if (section === 'tally') {
      setTallyState(prev => ({ ...prev, retryCount: newRetryCount }));
    } else {
      setConversationState(prev => ({ ...prev, retryCount: newRetryCount }));
    }

    // Retry with exponential backoff
    const delay = computeBackoff(newRetryCount);
    try {
      await scheduler.wait(delay, abortControllerRef.current?.signal);
      if (section === 'directions' || section === 'tally') {
        fetchCompass();
      }
      // Conversation retry is handled in ConversationSection
    } catch (error) {
      // Request was aborted, don't retry
      if (isAbortError(error)) {
        return;
      }
      throw error;
    }
  }, [fetchCompass, scheduler]);

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      // Could add a toast here later
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  const handleVoteSubmit = async (optionId: string) => {
    if (!poll || isSubmitting) return;

    compassAnalytics.alignSubmit(poll.id, optionId);

    try {
      setIsSubmitting(true);
      setVoteError(null);

      const voteData = await castVote(poll.id, optionId);

      // Update state
      setMyVote(voteData);
      setMyAlignment(optionId);
      setSelectedOptionId(optionId);

      // Track analytics - check if this is a change alignment
      if (myVote) {
        compassAnalytics.changeAlignment(poll.id, optionId);
      } else {
        compassAnalytics.alignSuccess(poll.id, optionId);
      }

      // Refresh results
      try {
        const resultsData = await getResults(poll.id);
        if (resultsData && resultsData.options) {
          const tallyData = resultsData.options.map(option => ({
            optionId: option.option_id,
            count: option.votes
          }));
          setTally(tallyData);
        }
      } catch {
        console.log('Could not refresh results');
      }
    } catch (err: unknown) {
      const error = err as { message: string | Array<unknown> };
      console.error('Failed to cast vote:', error);

      // Handle different error message formats
      let errorMessage = 'Failed to align with this direction';
      if (error.message) {
        if (Array.isArray(error.message)) {
          // If message is an array (validation errors), join them
          errorMessage = error.message.map((item: unknown) =>
            typeof item === 'string' ? item : (item as { msg?: string })?.msg || 'Validation error'
          ).join(', ');
        } else if (typeof error.message === 'string') {
          errorMessage = error.message;
        }
      }

      setVoteError(errorMessage);
      compassAnalytics.error('vote', errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChangeAlignmentTo = (nextDirectionId: string) => {
    setSelectedOptionId(nextDirectionId);
    setVoteError(null);
    // The actual vote submission will happen when the user clicks the submit button
  };

  // Convert options to directions format
  const directions: Direction[] = options.map(option => ({
    id: option.id,
    title: option.text,
    description: option.id.startsWith('placeholder')
      ? 'This direction option will be available soon.'
      : 'Choose this direction to align with the community\'s long-term vision.',
    votes: tally.find(t => t.optionId === option.id)?.count || 0
  }));

  const totalVotes = tally.reduce((sum, item) => sum + item.count, 0);

  // Show error state if main directions failed (regardless of other section states)
  if (directionsState.status === 'error') {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto text-center py-12">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">{compassCopy.errorTitle}</h2>
          <p className="text-gray-700 mb-6">{directionsState.error || compassCopy.errorBody}</p>
          <Button onClick={() => retrySection('directions')} variant="primary">
            {compassCopy.retry}
          </Button>
        </div>
      </div>
    );
  }

  // Show loading skeleton if main sections are loading
  if (directionsState.status === 'loading' || tallyState.status === 'loading') {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <CompassSkeleton />
        </div>
      </div>
    );
  }



  if (!poll) {
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <main className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              onClick={() => navigate('/proposals')}
              className="text-gray-700 hover:text-gray-900"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Proposals
            </Button>
          </div>

          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{cc.title}</h1>

          {/* Labels */}
          {flags.labelsEnabled && poll.labels && poll.labels.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {poll.labels.map(label => (
                <LabelChip
                  key={label.id}
                  label={label}
                  size="sm"
                />
              ))}
            </div>
          )}

          <p className="mt-1 text-gray-700">{cc.framing}</p>
        </div>

        {/* The Question */}
        <section className="mt-6">
          <h2 className="text-lg font-semibold">{cc.questionHeading}</h2>
          <p className="mt-2 whitespace-pre-line text-gray-800">{cc.questionBody}</p>
        </section>

        {/* Vote Error */}
        {voteError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-red-700 mb-2">{voteError}</p>
            <Button onClick={() => setVoteError(null)} variant="ghost" size="sm">
              Dismiss
            </Button>
          </div>
        )}

        {/* Direction Options */}
        <section className="mt-6">
          <h2 className="text-lg font-semibold">Choose a direction to align with</h2>

          {directionsState.status === 'empty' ? (
            <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
              <p className="text-gray-700">{compassCopy.directionsEmpty}</p>
            </div>
          ) : (
            <div className="mt-3 grid gap-4 md:grid-cols-2">
              <DirectionCard
                title={cc.dir1.title}
                summary={cc.dir1.summary}
                readMoreHeading={cc.dir1.readMoreHeading}
                rationale={cc.dir1.rationale}
                counterHeading={cc.dir1.counterHeading}
                counters={cc.dir1.counters}
                direction={directions[0]}
                aligned={myVote?.option_id === directions[0]?.id}
                onAlign={() => handleVoteSubmit(directions[0]?.id)}
                onChangeAlignment={() => handleChangeAlignmentTo(directions[0]?.id)}
                isSubmitting={isSubmitting}
                disabled={!!myAlignment}
              />
              <DirectionCard
                title={cc.dir2.title}
                summary={cc.dir2.summary}
                readMoreHeading={cc.dir2.readMoreHeading}
                rationale={cc.dir2.rationale}
                counterHeading={cc.dir2.counterHeading}
                counters={cc.dir2.counters}
                direction={directions[1]}
                aligned={myVote?.option_id === directions[1]?.id}
                onAlign={() => handleVoteSubmit(directions[1]?.id)}
                onChangeAlignment={() => handleChangeAlignmentTo(directions[1]?.id)}
                isSubmitting={isSubmitting}
                disabled={!!myAlignment}
              />
            </div>
          )}
        </section>

        {/* Tally */}
        <section className="mt-6">
          <h2 className="text-lg font-semibold">{compassCopy.tallyTitle}</h2>

          {tallyState.status === 'error' ? (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
              <p className="text-red-700 mb-2">{tallyState.error}</p>
              <Button onClick={() => retrySection('tally')} variant="ghost" size="sm">
                {compassCopy.retry}
              </Button>
            </div>
          ) : totalVotes > 0 ? (
            <div className="p-6 bg-white rounded-xl border border-gray-200" data-testid="tally-section">
              <CompassTally
                items={tally.map(item => ({
                  id: item.optionId,
                  title: options.find(o => o.id === item.optionId)?.text || 'Unknown',
                  count: item.count
                }))}
                total={totalVotes}
              />
            </div>
          ) : (
            <div className="p-6 bg-gray-50 rounded-xl border border-gray-200 text-center">
              <p className="text-gray-700">{compassCopy.tallyEmpty}</p>
            </div>
          )}
        </section>

        {/* Community Examples (hardcoded mode only) */}
        {import.meta.env.VITE_USE_HARDCODED_DATA === 'true' && (
          <section className="mt-6">
            <h2 className="text-lg font-semibold">{cc.communityExamplesHeading}</h2>
            <div className="mt-3 p-4 bg-blue-50 rounded-xl border border-blue-200">
              <ul className="space-y-2 text-sm text-gray-700">
                {cc.communityExamples.map((example, i) => (
                  <li key={i} className="italic">"{example}"</li>
                ))}
              </ul>
            </div>
          </section>
        )}

        {/* Community Reasoning */}
        <ConversationSection
          pollId={poll.id}
          directions={directions}
          myAlignment={myAlignment}
          onStateChange={setConversationState}
          onRetry={() => retrySection('conversation')}
        />

        {/* Background & Context */}
        <section className="mt-8">
          <h2 className="text-lg font-semibold">{cc.backgroundHeading}</h2>
          <p className="mt-2 text-gray-800">{cc.backgroundSummary}</p>
          <Expandable id="background-more">
            <ul className="list-disc pl-5">
              {cc.backgroundReadMore.map((x, i) => (<li key={i}>{x}</li>))}
            </ul>
          </Expandable>
        </section>

        {/* Meta Info */}
        <section>
          <div className="flex items-center justify-between p-6 bg-gray-50 rounded-xl border border-gray-200">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Calendar className="w-4 h-4" />
                <span>Created {new Date(poll.created_at).toLocaleDateString()}</span>
              </div>
              {poll.updated_at && poll.updated_at !== poll.created_at && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="w-4 h-4" />
                  <span>Updated {new Date(poll.updated_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>
            <Button
              variant="ghost"
              onClick={handleShare}
              className="text-gray-600 hover:text-gray-800"
            >
              <Share2 className="w-4 h-4 mr-2" />
              {compassCopy.share}
            </Button>
          </div>
        </section>
      </main>
    </div>
  );
}
