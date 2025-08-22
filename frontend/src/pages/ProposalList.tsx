import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Plus, Compass, Target } from 'lucide-react';
import { listPolls } from '../lib/api';
import type { Poll } from '../types';
import Button from '../components/ui/Button';
import Empty from '../components/ui/Empty';
import { useToast } from '../components/ui/useToast';
import ProposalCard from '../components/ProposalCard';
import LevelSection from '../components/LevelSection';
import LevelFilter, { type LevelFilterType } from '../components/LevelFilter';

export default function ProposalList() {
  const [polls, setPolls] = useState<Poll[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<LevelFilterType>('all');
  const { error: showError } = useToast();

  // Check if we should use hardcoded data
  const useHardcodedData = import.meta.env.VITE_USE_HARDCODED_DATA === 'true';

  // Hardcoded fallback data for development
  const hardcodedPolls: Poll[] = [
    {
              id: 'ai-edu-001',
                      title: 'AI in Education: A Tool for Stronger Learning',
        description: 'Our community leans toward using AI to support teachers and students—freeing teachers from routine tasks, offering tailored explanations, and improving access—while keeping education human at its core.',
      created_by: 'hardcoded-user-1',
      created_at: '2025-01-10T10:00:00Z',
      updated_at: '2025-01-10T10:00:00Z',
      is_active: true,
      end_date: '2025-02-15T00:00:00Z',
      decision_type: 'level_a',
      direction_choice: 'Placeholder',
      your_vote_status: {
        status: 'voted',
        resolved_vote_path: ['hardcoded-user-1']
      }
    },
    {
      id: 'hardcoded-2',
      title: 'Level B Principle (Placeholder)',
      description: 'This is a placeholder example for Level B. It demonstrates how community-level or technical sub-questions could be explored.',
      created_by: 'hardcoded-user-2',
      created_at: '2025-01-15T11:20:00Z',
      updated_at: '2025-01-15T11:20:00Z',
      is_active: true,
      end_date: '2025-02-28T00:00:00Z',
      decision_type: 'level_b',
      your_vote_status: {
        status: 'none',
        resolved_vote_path: []
      }
    }
  ];

  useEffect(() => {
    if (useHardcodedData) {
      setPolls(hardcodedPolls);
      setLoading(false);
    } else {
      fetchPolls();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional one-time initialization
  }, [useHardcodedData]);

  const fetchPolls = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedPolls = await listPolls();
      setPolls(fetchedPolls);
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to load polls:', error.message);
      setError(error.message);
      showError('Failed to load community ideas');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="gov-container gov-section">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gov-primary mx-auto mb-4"></div>
          <p className="text-gov-text-muted">Loading community ideas...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="gov-container gov-section">
        <div className="text-center py-12">
          <p className="text-gov-danger mb-4">Error: {error}</p>
          <Button onClick={fetchPolls}>Retry</Button>
        </div>
      </div>
    );
  }

  // Filter polls based on active filter
  const filteredPolls = polls.filter(poll => {
    if (activeFilter === 'all') return true;
    return poll.decision_type === activeFilter;
  });

  const levelAPolls = polls.filter(poll => poll.decision_type === 'level_a');
  const levelBPolls = polls.filter(poll => poll.decision_type === 'level_b');

  return (
    <div className="gov-container gov-section">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gov-secondary rounded-md flex items-center justify-center">
            <FileText className="w-5 h-5 text-gov-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gov-primary">All Community Ideas</h1>
            <p className="text-gov-text-muted mt-1">Browse all principles and actions together</p>
          </div>
        </div>
        <Link to="/proposals/new">
          <Button variant="primary">
            <Plus className="w-4 h-4 mr-2" />
            Share Your Idea
          </Button>
        </Link>
      </div>

      {/* Level Filter */}
      <div className="mb-8">
        <LevelFilter
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          className="mb-6"
        />
      </div>

      {polls.length === 0 ? (
        <Empty
          icon={<FileText className="w-8 h-8" />}
          title="No community ideas yet"
          subtitle="Be the first to share an idea that could make your community better."
          action={
            <Link to="/proposals/new">
              <Button variant="primary">
                <Plus className="w-4 h-4 mr-2" />
                Share Your First Idea
              </Button>
            </Link>
          }
        />
      ) : (
        <div className="space-y-12">
          {/* Principles Section */}
          {levelAPolls.length > 0 && (activeFilter === 'all' || activeFilter === 'level_a') && (
            <LevelSection level="a" title="Long-Term Direction">
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {levelAPolls.map((poll, index) => (
                  <ProposalCard key={`level-a-${poll.id}`} poll={poll} index={index} />
                ))}
              </div>
              <div className="mt-6 text-center">
                <Link to="/principles">
                  <Button variant="ghost" className="text-sky-600 hover:text-sky-700">
                    <Compass className="w-4 h-4 mr-2" />
                    See All Principles
                  </Button>
                </Link>
              </div>
            </LevelSection>
          )}

          {/* Actions Section */}
          {levelBPolls.length > 0 && (activeFilter === 'all' || activeFilter === 'level_b') && (
            <LevelSection level="b" title="Short-Term Decisions">
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {levelBPolls.map((poll, index) => (
                  <ProposalCard key={`level-b-${poll.id}`} poll={poll} index={index} />
                ))}
              </div>
              <div className="mt-6 text-center">
                <Link to="/actions">
                  <Button variant="ghost" className="text-green-600 hover:text-green-700">
                    <Target className="w-4 h-4 mr-2" />
                    See All Actions
                  </Button>
                </Link>
              </div>
            </LevelSection>
          )}

          {/* Empty state for filtered results */}
          {filteredPolls.length === 0 && polls.length > 0 && (
            <div className="text-center py-12">
              <p className="text-gov-text-muted mb-4">
                No {activeFilter === 'level_a' ? 'principles' : 'actions'} found.
              </p>
              <Button onClick={() => setActiveFilter('all')} variant="secondary">
                Show All Levels
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
