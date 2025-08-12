import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, FileText, BarChart3, MessageCircle, CheckCircle, XCircle, Minus } from 'lucide-react';
import { getPoll, getPollOptions, getMyVoteForPoll, castVote, getResults } from '../lib/api';
import type { Poll, PollOption, Vote, PollResults } from '../types';
import Button from '../components/ui/Button';
import ProposalComments from '../components/ProposalComments';
import { useToast } from '../components/ui/useToast';

export default function ProposalDetail() {
  const { id } = useParams<{ id: string }>();
  const [poll, setPoll] = useState<Poll | null>(null);
  const [options, setOptions] = useState<PollOption[]>([]);
  const [myVote, setMyVote] = useState<Vote | null>(null);
  const [results, setResults] = useState<PollResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState<string | null>(null);
  const { success, error: showError } = useToast();

  useEffect(() => {
    if (id) {
      fetchData();
    }
  }, [id]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [pollData, optionsData, voteData, resultsData] = await Promise.all([
        getPoll(id!),
        getPollOptions(id!),
        getMyVoteForPoll(id!),
        getResults(id!)
      ]);
      setPoll(pollData);
      setOptions(optionsData);
      setMyVote(voteData);
      setResults(resultsData);
    } catch (err: unknown) {
      const error = err as { message: string };
      showError('Failed to load proposal');
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (optionId: string) => {
    if (!poll || voting) return;

    try {
      setVoting(optionId);
      await castVote(poll.id, optionId);
      await fetchData(); // Refresh data
      success('Vote cast successfully');
    } catch (err: unknown) {
      const error = err as { message: string };
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

  return (
    <div className="container mx-auto px-4 pb-20 sm:pb-8">
      {/* Header */}
      <div className="mb-8">
        <Link to="/proposals" className="inline-flex items-center gap-2 text-muted hover:text-white transition-colors mb-4">
          <ArrowLeft className="w-4 h-4" />
          Back to Proposals
        </Link>
        <h1 className="text-3xl font-bold text-white mb-4">{poll.title}</h1>
        <p className="text-muted leading-relaxed">{poll.description}</p>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Details Section */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <FileText className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold text-white">Details</h2>
            </div>
            <div className="p-6 bg-surface border border-border rounded-lg">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <span className="text-sm text-muted">Created</span>
                  <p className="font-medium text-white">{new Date(poll.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <span className="text-sm text-muted">Updated</span>
                  <p className="font-medium text-white">{new Date(poll.updated_at).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          </section>

          {/* Results Section */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <BarChart3 className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold text-white">Results</h2>
            </div>
            <div className="p-6 bg-surface border border-border rounded-lg space-y-4">
              {results && results.total_votes > 0 ? (
                options.map((option) => {
                  const percentage = getVotePercentage(option.id);
                  return (
                    <div key={option.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-white">{option.text}</span>
                        <span className="text-sm text-muted">{percentage.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-border rounded-full h-2 overflow-hidden">
                        <motion.div
                          className="h-full bg-primary rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${percentage}%` }}
                          transition={{ duration: 0.8, ease: "easeOut" }}
                        />
                      </div>
                      <div className="text-xs text-muted">
                        {results.options.find(o => o.option_id === option.id)?.votes || 0} votes
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-muted text-center py-4">No votes yet</p>
              )}
            </div>
          </section>

          {/* Discussion Section */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <MessageCircle className="w-5 h-5 text-primary" />
              <h2 className="text-xl font-semibold text-white">Discussion</h2>
            </div>
            <ProposalComments pollId={poll.id} />
          </section>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-8">
            <div className="p-6 bg-surface border border-border rounded-lg space-y-4">
              <h3 className="font-semibold text-white">Vote</h3>
              {isVoted ? (
                <div className="text-center py-4">
                  <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                  <p className="text-sm text-muted">You've voted</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {options.map((option) => (
                    <Button
                      key={option.id}
                      onClick={() => handleVote(option.id)}
                      disabled={isClosed || voting === option.id}
                      loading={voting === option.id}
                      className="w-full justify-start"
                      variant={option.text.toLowerCase().includes('yes') ? 'primary' : 'ghost'}
                    >
                      {option.text.toLowerCase().includes('yes') && <CheckCircle className="w-4 h-4 mr-2" />}
                      {option.text.toLowerCase().includes('no') && <XCircle className="w-4 h-4 mr-2" />}
                      {option.text.toLowerCase().includes('abstain') && <Minus className="w-4 h-4 mr-2" />}
                      {option.text}
                    </Button>
                  ))}
                </div>
              )}
              {isClosed && (
                <div className="text-center py-2">
                  <span className="text-xs text-muted bg-muted px-2 py-1 rounded">Voting closed</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Sticky Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-surface/95 backdrop-blur border-t border-border py-3 px-4 sm:hidden" style={{ paddingBottom: 'calc(0.75rem + env(safe-area-inset-bottom))' }}>
        <div className="flex gap-2">
          {isVoted ? (
            <div className="flex-1 text-center py-2">
              <CheckCircle className="w-5 h-5 text-green-500 mx-auto mb-1" />
              <p className="text-xs text-muted">You've voted</p>
            </div>
          ) : (
            options.map((option) => (
              <Button
                key={option.id}
                onClick={() => handleVote(option.id)}
                disabled={isClosed || voting === option.id}
                loading={voting === option.id}
                size="sm"
                className="flex-1"
                variant={option.text.toLowerCase().includes('yes') ? 'primary' : 'ghost'}
              >
                {option.text.toLowerCase().includes('yes') && <CheckCircle className="w-4 h-4 mr-1" />}
                {option.text.toLowerCase().includes('no') && <XCircle className="w-4 h-4 mr-1" />}
                {option.text.toLowerCase().includes('abstain') && <Minus className="w-4 h-4 mr-1" />}
                {option.text}
              </Button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
