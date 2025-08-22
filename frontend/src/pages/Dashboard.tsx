import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Users,
  Vote,
  MessageCircle,
  TrendingUp,
  Shield,
  Globe,
  ArrowRight,
  BarChart3,
  Heart,
  Sparkles,
  Handshake,
  Lightbulb,
  Compass,
  Target
} from 'lucide-react';
import { listPolls, getContentPrinciples, getContentActions, getSafeDelegationSummary, setDelegation, listLabels } from '../lib/api';
import { trackDelegationSummaryLoaded } from '../api/delegationsApi';
import type { Poll, Label } from '../types';
import type { SafeDelegationSummary } from '../lib/api';
import type { PrincipleItem, ActionItem } from '../types/content';
import Button from '../components/ui/Button';
import { useToast } from '../components/ui/useToast';
import ProposalCard from '../components/ProposalCard';
import ContentList from '../components/content/ContentList';
import LabelChip from '../components/ui/LabelChip';
import { Skeleton } from '../components/ui/Skeleton';
import { flags } from '../config/flags';
import { useCurrentUser } from '../hooks/useCurrentUser';
import TransparencyPanel from '../components/delegations/TransparencyPanel';

import type { DelegationPerLabel } from '../types/http';

const getPerLabel = (s?: { per_label?: DelegationPerLabel[] } | null): DelegationPerLabel[] =>
  Array.isArray(s?.per_label) ? s!.per_label : [];

export default function Dashboard() {
  const [recentPolls, setRecentPolls] = useState<Poll[]>([]);
  const [principles, setPrinciples] = useState<PrincipleItem[]>([]);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [delegationSummary, setDelegationSummary] = useState<SafeDelegationSummary | null>(null);
  const [labels, setLabels] = useState<Label[]>([]);
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(true);
  const [contentError, setContentError] = useState<string | null>(null);
  const [delegationLoading, setDelegationLoading] = useState(false);
  const [delegationSummaryLoading, setDelegationSummaryLoading] = useState(false);
  const [transparencyOpen, setTransparencyOpen] = useState(false);
  const [transparencyDefaultTab, setTransparencyDefaultTab] = useState<'chains' | 'inbound' | 'health'>('health');
  const { error: showError, success: showSuccess } = useToast();
  const telemetrySentRef = useRef(false);
  const { user, loading: userLoading } = useCurrentUser();

  // Counts for dashboard sections
  const levelACount = recentPolls.filter(poll => poll.decision_type === 'level_a').length;
  const levelBCount = recentPolls.filter(poll => poll.decision_type === 'level_b').length;

  const fetchRecentPolls = useCallback(async () => {
    try {
      setLoading(true);
      const polls = await listPolls();
      // Get the 6 most recent polls
      const recent = polls.slice(0, 6);
      setRecentPolls(recent);
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to load recent polls:', error.message);
      // Don't show error toast to avoid dependency issues
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    console.log('[DEBUG] Dashboard useEffect - user:', user, 'userLoading:', userLoading, 'labelsEnabled:', flags.labelsEnabled);

    // Only fetch polls if user is authenticated
    if (!userLoading && user) {
      fetchRecentPolls();
    } else if (!userLoading && !user) {
      // Clear polls when not authenticated
      setRecentPolls([]);
      setLoading(false);
    }

    if (!flags.useDemoContent) {
      fetchContent();
    } else {
      setContentLoading(false);
    }
    // Always fetch delegation data if labels are enabled and user is authenticated
    if (flags.labelsEnabled && !userLoading && user) {
      console.log('[DEBUG] Dashboard: Fetching delegation data (safe endpoint)');
      fetchDelegationSummary();
      fetchLabels();
    } else if (flags.labelsEnabled && !userLoading && !user) {
      // Clear delegation data when not authenticated
      console.log('[DEBUG] Dashboard: Clearing delegation data - not authenticated');
      setDelegationSummary(null);
      setLabels([]);
    } else if (!flags.labelsEnabled && !userLoading) {
      // Clear delegation data when labels are disabled
      console.log('[DEBUG] Dashboard: Clearing delegation data - labels disabled');
      setDelegationSummary(null);
      setLabels([]);
    }
  }, [user, userLoading, fetchRecentPolls]);

  const fetchContent = useCallback(async () => {
    try {
      setContentLoading(true);
      setContentError(null);
      const [principlesData, actionsData] = await Promise.all([
        getContentPrinciples(),
        getContentActions()
      ]);
      setPrinciples(principlesData);
      setActions(actionsData);
    } catch (err) {
      console.error('Failed to load content:', err);
      setContentError('Failed to load content');
    } finally {
      setContentLoading(false);
    }
  }, []);

  const fetchDelegationSummary = useCallback(async () => {
    try {
      setDelegationSummaryLoading(true);
      console.log('[DEBUG] fetchDelegationSummary: Starting safe API call');
      const summary = await getSafeDelegationSummary();
      console.log('[DEBUG] fetchDelegationSummary: Response:', summary);

      if (summary.meta?.errors?.length) {
        console.warn('[DEBUG] fetchDelegationSummary: Errors in response:', summary.meta.errors);
        if (summary.meta.trace_id) {
          console.log('[DEBUG] fetchDelegationSummary: Trace ID for debugging:', summary.meta.trace_id);
        }
      }

      setDelegationSummary(summary);

      // Track telemetry once per mount
      if (!telemetrySentRef.current) {
        trackDelegationSummaryLoaded(!!summary?.ok);
        telemetrySentRef.current = true;
      }

      // Show non-blocking warning if there are errors but some data is available
      if (!summary.ok && summary.meta?.errors?.length) {
        const hasData = summary.global_delegate || (summary.per_label && summary.per_label.length > 0);
        if (hasData) {
          console.warn('Delegation summary is partially available with errors:', summary.meta.errors);
        }
      }

    } catch (err) {
      console.error('[DEBUG] fetchDelegationSummary: Unexpected error:', err);
      // Set a minimal error state with friendly fallback
      setDelegationSummary({
        ok: false,
        counts: { mine: 0, inbound: 0 },
        meta: {
          errors: ['unexpected_error'],
          generated_at: new Date().toISOString()
        }
      });
    } finally {
      setDelegationSummaryLoading(false);
    }
  }, []);

  const fetchLabels = useCallback(async () => {
    try {
      const labelsData = await listLabels();
      setLabels(labelsData);
    } catch (err) {
      console.error('Failed to load labels:', err);
    }
  }, []);

  const handleSetDelegation = async (delegateUsername: string, labelSlug?: string) => {
    try {
      setDelegationLoading(true);
      await setDelegation(delegateUsername, labelSlug);

      // Always refresh delegation summary (it handles auth gracefully)
      await fetchDelegationSummary();

      showSuccess(`Delegation ${labelSlug ? `for ${labelSlug}` : 'globally'} set successfully`);
    } catch (err: unknown) {
      const error = err as { message?: string };
      showError(error?.message || 'Failed to set delegation');
    } finally {
      setDelegationLoading(false);
    }
  };

  const handleRetry = async () => {
    setDelegationSummaryLoading(true);
    try {
      const summary = await getSafeDelegationSummary();
      setDelegationSummary(summary);

      // Track telemetry once per mount
      if (!telemetrySentRef.current) {
        trackDelegationSummaryLoaded(!!summary?.ok);
        telemetrySentRef.current = true;
      }
    } catch (err) {
      console.error('Failed to retry delegation summary:', err);
    } finally {
      setDelegationSummaryLoading(false);
    }
  };

  // DelegationForm Component
  const DelegationForm = ({ onSubmit, loading, placeholder }: {
    onSubmit: (username: string) => void;
    loading: boolean;
    placeholder: string;
  }) => {
    const [username, setUsername] = useState('');
    const [isOpen, setIsOpen] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      if (username.trim()) {
        onSubmit(username.trim());
        setUsername('');
        setIsOpen(false);
      }
    };

    if (!isOpen) {
      return (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsOpen(true)}
          disabled={loading}
          className="text-purple-600 hover:text-purple-700"
        >
          Set delegation
        </Button>
      );
    }

    return (
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder={placeholder}
          className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
          disabled={loading}
        />
        <Button
          type="submit"
          variant="ghost"
          size="sm"
          disabled={loading || !username.trim()}
          className="text-purple-600 hover:text-purple-700"
        >
          {loading ? 'Saving...' : 'Save'}
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setIsOpen(false)}
          disabled={loading}
          className="text-gray-500 hover:text-gray-700"
        >
          Cancel
        </Button>
      </form>
    );
  };

  const communityStories = [
    {
      icon: <Heart className="w-6 h-6" />,
      title: "Placeholder Story 1",
      description: "This is a placeholder story for demonstration purposes"
    },
    {
      icon: <Handshake className="w-6 h-6" />,
      title: "Placeholder Story 2",
      description: "This is a placeholder story for demonstration purposes"
    },
    {
      icon: <Lightbulb className="w-6 h-6" />,
      title: "Placeholder Story 3",
      description: "This is a placeholder story for demonstration purposes"
    }
  ];

  const waysToParticipate = [
    {
      icon: <Vote className="w-6 h-6" />,
      title: "Share Your Voice",
      description: "Cast your vote on decisions that shape your community's future"
    },
    {
      icon: <MessageCircle className="w-6 h-6" />,
      title: "Join the Conversation",
      description: "Share ideas, ask questions, and connect with your neighbors"
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Build Trust Together",
      description: "Delegate your voice to community members you trust and respect"
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "See Your Impact",
      description: "Watch how your participation helps build a stronger community"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Safe & Transparent",
      description: "Every decision is open and accountable to build lasting trust"
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Local to Global",
      description: "Start with your neighborhood, inspire communities everywhere"
    }
  ];

  return (
    <>
    <div className="gov-container gov-section">
      {/* Hero Section - Government Style */}
      <div className="text-center mb-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 text-gov-primary">
            Welcome to the Commons
          </h1>
          <p className="text-xl text-gov-text-muted max-w-3xl mx-auto leading-relaxed">
            Here's where ideas are shared, debated, and decided. Every voice matters — and every decision is public.
          </p>
        </motion.div>
      </div>

      <div className="grid gap-12 lg:grid-cols-2">
        {/* Left Column - Community Focus */}
        <div>
          {/* About Section - Government Style */}
          <div className="gov-card mb-8">
            <div className="mb-4">
              <h2 className="text-2xl font-semibold text-gov-primary mb-4 flex items-center gap-3">
                <div className="w-8 h-8 bg-gov-secondary rounded-md flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-gov-primary" />
                </div>
                About The Commons
              </h2>
            </div>
            <div className="space-y-3">
              <p className="text-gov-text-muted leading-relaxed">
                The Commons is an open space for making community decisions.
              </p>
              <p className="text-gov-text-muted leading-relaxed">
                We keep principles separate from immediate actions, so we don't confuse long-term direction with short-term steps.
              </p>
              <p className="text-gov-text-muted leading-relaxed">
                You can propose, discuss, vote, or delegate. Everything is transparent and reversible.
              </p>
            </div>
          </div>

          {/* Community Stories - Government Style */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-gov-primary mb-6">Community Success Stories</h2>
            <div className="space-y-4">
              {communityStories.map((story, index) => (
                <motion.div
                  key={story.title}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="gov-card gov-card-hover"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-gov-secondary rounded-md flex items-center justify-center flex-shrink-0">
                      {story.icon}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gov-text mb-2">{story.title}</h3>
                      <p className="text-gov-text-muted leading-relaxed">{story.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Ways to Participate - Government Style */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-gov-primary mb-6">Ways to Participate</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {waysToParticipate.map((way, index) => (
                <motion.div
                  key={way.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="gov-card gov-card-hover"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 bg-gov-secondary rounded-md flex items-center justify-center flex-shrink-0">
                      {way.icon}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gov-text mb-2">{way.title}</h3>
                      <p className="text-sm text-gov-text-muted leading-relaxed">{way.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Quick Actions - Government Style */}
          <div className="gov-card">
            <h2 className="text-xl font-semibold text-gov-primary mb-4">Ready to Get Started?</h2>
            <div className="space-y-3">
              <Link to="/proposals/new">
                <Button className="w-full justify-start" variant="primary" size="lg">
                  <Lightbulb className="w-5 h-5 mr-3" />
                  Start a Proposal
                </Button>
              </Link>
              <Link to="/proposals">
                <Button className="w-full justify-start" variant="secondary" size="lg">
                  <BarChart3 className="w-5 h-5 mr-3" />
                  See Proposals
                </Button>
              </Link>
              <Link to="/activity">
                <Button className="w-full justify-start" variant="ghost" size="lg">
                  <TrendingUp className="w-5 h-5 mr-3" />
                  Community Activity
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Right Column - Content & Recent Activity */}
        <div className="space-y-8">
          {/* Content Sections (when not using demo content) */}
          {!flags.useDemoContent && (
            <>
              <ContentList
                title="Community Principles"
                items={principles}
                loading={contentLoading}
                error={contentError}
                compact={true}
                emptyMessage="Add your first principle"
                className="mb-6"
              />
              <ContentList
                title="Community Actions"
                items={actions}
                loading={contentLoading}
                error={contentError}
                compact={true}
                emptyMessage="Add your first action"
                className="mb-6"
              />
            </>
          )}

          {/* Label-Specific Delegations */}
          {flags.labelsEnabled && user && (
            <div className="gov-card mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gov-primary flex items-center gap-2">
                  <div className="w-6 h-6 bg-purple-100 rounded flex items-center justify-center">
                    <Users className="w-4 h-4 text-purple-600" />
                  </div>
                  Your Delegations by Topic
                </h3>
              </div>

              {userLoading || delegationSummaryLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-12 w-full" />
                  <div className="grid gap-3 md:grid-cols-2">
                    <Skeleton className="h-16 w-full" />
                    <Skeleton className="h-16 w-full" />
                  </div>
                </div>
              ) : !delegationSummary?.ok ? (
                <div className="p-4 text-center">
                  <div className="text-gray-500 mb-2">Delegation summary unavailable</div>
                  <div className="text-xs text-gray-400 mb-3">Try again now or open Transparency to inspect live data.</div>
                  <div className="flex justify-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleRetry}
                      disabled={delegationSummaryLoading}
                    >
                      Retry
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setTransparencyDefaultTab('health');
                        setTransparencyOpen(true);
                      }}
                      className="text-purple-600 hover:text-purple-700"
                    >
                      Open Transparency
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                {/* Empty State CTA */}
                {delegationSummary?.ok && delegationSummary?.counts?.mine === 0 && delegationSummary?.counts?.inbound === 0 && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-center">
                    <div className="text-blue-800 mb-2">No delegations yet</div>
                    <div className="text-blue-600 text-sm mb-3">Delegate all power for 4 years, or start with a single field. You can revoke anytime.</div>
                    <div className="flex justify-center gap-2">
                      <Link to="/delegations">
                        <Button variant="secondary" size="sm" className="text-blue-600 hover:text-blue-700">
                          Start a delegation
                        </Button>
                      </Link>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          setTransparencyDefaultTab('chains');
                          setTransparencyOpen(true);
                        }}
                        className="text-purple-600 hover:text-purple-700"
                      >
                        Open Transparency
                      </Button>
                    </div>
                  </div>
                )}

                {/* Global Delegation */}
                {delegationSummary?.global_delegate && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-sm font-medium text-blue-800">Global Delegate:</span>
                        <span className="ml-2 text-sm text-blue-600">
                          {delegationSummary.global_delegate?.delegatee_username || 'Not set'}
                        </span>
                      </div>
                      {user && (
                        <DelegationForm
                          onSubmit={(username) => handleSetDelegation(username)}
                          loading={delegationLoading}
                          placeholder="Set global delegate"
                        />
                      )}
                    </div>
                  </div>
                )}

                {/* Per-Label Delegations */}
                <div className="grid gap-3 md:grid-cols-2">
                  {labels.map(label => {
                    const perLabel = getPerLabel(delegationSummary);
                    const labelDelegation = perLabel.find(
                      d => d.label.slug === label.slug
                    );
                    return (
                      <div key={label.id} className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <LabelChip label={label} size="sm" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">
                            {labelDelegation?.delegate.username || 'Not set'}
                          </span>
                          {user && (
                            <DelegationForm
                              onSubmit={(username) => handleSetDelegation(username, label.slug)}
                              loading={delegationLoading}
                              placeholder={`Set ${label.name} delegate`}
                            />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
              )}
            </div>
          )}

          {/* Recent Community Activity */}
          <div>
            <h2 className="text-2xl font-semibold text-gov-primary mb-6">Recent Community Activity</h2>
          {userLoading ? (
            <div className="space-y-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="gov-card animate-pulse">
                  <div className="h-4 bg-gray-200 rounded mb-3"></div>
                  <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                </div>
              ))}
            </div>
          ) : !user ? (
            <div className="gov-card">
              <div className="text-center py-8">
                <p className="text-gov-text-muted mb-2">Sign in to see recent community activity</p>
                <Link to="/login">
                  <Button variant="primary">Sign In</Button>
                </Link>
              </div>
            </div>
          ) : loading ? (
            <div className="space-y-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="gov-card animate-pulse">
                  <div className="h-4 bg-gray-200 rounded mb-3"></div>
                  <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                </div>
              ))}
            </div>
          ) : recentPolls.length > 0 ? (
            <div className="space-y-6">
              {/* Principles Section */}
              <div className="gov-card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gov-primary flex items-center gap-2">
                    <div className="w-6 h-6 bg-sky-100 rounded flex items-center justify-center">
                      <Compass className="w-4 h-4 text-sky-600" />
                    </div>
                    Principles
                    <span className="text-sm font-normal text-gov-text-muted">({levelACount})</span>
                  </h3>
                  <Link to="/principles">
                    <Button variant="ghost" size="sm" className="text-sky-600 hover:text-sky-700">
                      See all
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                </div>
                {recentPolls.filter(poll => poll.decision_type === 'level_a').length > 0 ? (
                  <div className="space-y-3">
                    {recentPolls
                      .filter(poll => poll.decision_type === 'level_a')
                      .slice(0, 3)
                      .map((poll, index) => (
                        <ProposalCard key={`dashboard-principles-${poll.id}`} poll={poll} index={index} />
                      ))}
                  </div>
                ) : (
                  <p className="text-gov-text-muted text-sm">No principles yet. <Link to="/principles" className="text-sky-600 hover:underline">Start the first one</Link>.</p>
                )}
              </div>

              {/* Actions Section */}
              <div className="gov-card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gov-primary flex items-center gap-2">
                    <div className="w-6 h-6 bg-green-100 rounded flex items-center justify-center">
                      <Target className="w-4 h-4 text-green-600" />
                    </div>
                    Actions
                    <span className="text-sm font-normal text-gov-text-muted">({levelBCount})</span>
                  </h3>
                  <Link to="/actions">
                    <Button variant="ghost" size="sm" className="text-green-600 hover:text-green-700">
                      See all
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                </div>
                {recentPolls.filter(poll => poll.decision_type === 'level_b').length > 0 ? (
                  <div className="space-y-3">
                    {recentPolls
                      .filter(poll => poll.decision_type === 'level_b')
                      .slice(0, 3)
                      .map((poll, index) => (
                        <ProposalCard key={`dashboard-actions-${poll.id}`} poll={poll} index={index} />
                      ))}
                  </div>
                ) : (
                  <p className="text-gov-text-muted text-sm">No actions yet. <Link to="/actions" className="text-green-600 hover:underline">Start the first one</Link>.</p>
                )}
              </div>

              <div className="text-center pt-6">
                <Link to="/proposals">
                  <Button variant="secondary" className="text-gov-primary hover:text-gov-primary">
                    See All Community Proposals
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <div className="gov-card text-center">
              <div className="p-12">
                <div className="w-16 h-16 bg-gov-secondary rounded-lg flex items-center justify-center mx-auto mb-6">
                  <Users className="w-8 h-8 text-gov-primary" />
                </div>
                <h3 className="text-xl font-semibold text-gov-text mb-3">Be the First!</h3>
                <p className="text-gov-text-muted mb-6 leading-relaxed">
                  No proposals yet. Start the conversation by sharing your first idea with the community.
                </p>
                <Link to="/proposals/new">
                  <Button variant="primary" size="lg">
                    <Lightbulb className="w-5 h-5 mr-2" />
                    Share Your First Idea
                  </Button>
                </Link>
              </div>
            </div>
          )}
          </div>
        </div>
      </div>
    </div>

    <TransparencyPanel
      isOpen={transparencyOpen}
      onClose={() => setTransparencyOpen(false)}
      defaultTab={transparencyDefaultTab}
    />
    </>
  );
}
