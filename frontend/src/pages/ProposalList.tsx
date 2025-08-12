import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText, Plus } from 'lucide-react';
import { listPolls } from '../lib/api';
import type { Poll, DecisionType } from '../types';
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

  // Hardcoded data for testing UI logic
  const hardcodedPolls: Poll[] = [
    {
      id: 'hardcoded-1',
      title: 'Install protected bike lanes on Oak Street from Central Park to City Hall',
      description: 'Add dedicated, protected bicycle lanes along Oak Street to improve cyclist safety and encourage active transportation.',
      created_by: 'hardcoded-user-1',
      created_at: '2025-01-10T10:00:00Z',
      updated_at: '2025-01-10T10:00:00Z',
      is_active: true,
      end_date: '2025-02-15T00:00:00Z',
      decision_type: 'level_b',
      your_vote_status: {
        status: 'none',
        resolved_vote_path: []
      }
    },
    {
      id: 'hardcoded-2',
      title: 'Launch 12-month curbside compost pickup pilot in three neighborhoods',
      description: 'Begin organic waste collection service in Downtown, Westside, and Riverside neighborhoods to reduce landfill waste.',
      created_by: 'hardcoded-user-2',
      created_at: '2025-01-20T14:30:00Z',
      updated_at: '2025-01-20T14:30:00Z',
      is_active: false,
      end_date: '2025-03-01T00:00:00Z',
      decision_type: 'level_b',
      your_vote_status: {
        status: 'voted',
        resolved_vote_path: ['hardcoded-user-2']
      }
    },
    {
      id: 'hardcoded-3',
      title: 'Vision Zero Commitment',
      description: 'Commit to designing streets so that no one is killed or seriously injured in traffic.',
      created_by: 'hardcoded-user-3',
      created_at: '2025-01-05T09:15:00Z',
      updated_at: '2025-01-05T09:15:00Z',
      is_active: true,
      end_date: '2025-01-31T00:00:00Z',
      decision_type: 'level_a',
      direction_choice: 'Transportation Safety',
      your_vote_status: {
        status: 'delegated',
        resolved_vote_path: ['hardcoded-user-3', 'delegate-user-1'],
        final_delegatee_id: 'delegate-user-1'
      }
    },
    {
      id: 'hardcoded-4',
      title: 'Extend Saturday library hours from 5 PM to 8 PM for six-month trial',
      description: 'Extend operating hours at the main library to better serve students and working families.',
      created_by: 'hardcoded-user-4',
      created_at: '2025-01-15T11:20:00Z',
      updated_at: '2025-01-15T11:20:00Z',
      is_active: true,
      end_date: '2025-02-28T00:00:00Z',
      decision_type: 'level_b',
      your_vote_status: {
        status: 'none',
        resolved_vote_path: []
      }
    },
    {
      id: 'hardcoded-5',
      title: 'Open Government Policy',
      description: 'Publish public records and datasets unless there\'s a clear legal reason not to.',
      created_by: 'hardcoded-user-5',
      created_at: '2025-01-08T16:45:00Z',
      updated_at: '2025-01-08T16:45:00Z',
      is_active: true,
      end_date: '2025-02-10T00:00:00Z',
      decision_type: 'level_a',
      direction_choice: 'Government Transparency',
      your_vote_status: {
        status: 'voted',
        resolved_vote_path: ['hardcoded-user-5']
      }
    },
    {
      id: 'hardcoded-6',
      title: 'Plant 500 street trees along major bus routes',
      description: 'Add urban trees along transit corridors to improve air quality and provide shade for transit users.',
      created_by: 'hardcoded-user-6',
      created_at: '2025-01-12T13:30:00Z',
      updated_at: '2025-01-12T13:30:00Z',
      is_active: true,
      end_date: '2025-03-15T00:00:00Z',
      decision_type: 'level_b',
      your_vote_status: {
        status: 'none',
        resolved_vote_path: []
      }
    },
    {
      id: 'hardcoded-7',
      title: 'Environmental Stewardship Charter',
      description: 'Establish a comprehensive environmental policy framework for Riverbend, ensuring all future decisions consider ecological impact and sustainability.',
      created_by: 'hardcoded-user-7',
      created_at: '2025-01-03T08:00:00Z',
      updated_at: '2025-01-03T08:00:00Z',
      is_active: true,
      end_date: '2025-02-20T00:00:00Z',
      decision_type: 'level_a',
      direction_choice: 'Environmental Policy',
      your_vote_status: {
        status: 'voted',
        resolved_vote_path: ['hardcoded-user-7']
      }
    },
    {
      id: 'hardcoded-8',
      title: 'Affordable Housing First Policy',
      description: 'Prioritize affordable housing development in all zoning and development decisions.',
      created_by: 'hardcoded-user-8',
      created_at: '2025-01-07T14:20:00Z',
      updated_at: '2025-01-07T14:20:00Z',
      is_active: true,
      end_date: '2025-02-25T00:00:00Z',
      decision_type: 'level_a',
      direction_choice: 'Housing & Development',
      your_vote_status: {
        status: 'none',
        resolved_vote_path: []
      }
    },
    {
      id: 'hardcoded-9',
      title: 'Public Health Equity Framework',
      description: 'Ensure all public health initiatives prioritize equitable access and outcomes for all community members.',
      created_by: 'hardcoded-user-9',
      created_at: '2025-01-09T10:30:00Z',
      updated_at: '2025-01-09T10:30:00Z',
      is_active: true,
      end_date: '2025-03-05T00:00:00Z',
      decision_type: 'level_a',
      direction_choice: 'Public Health',
      your_vote_status: {
        status: 'delegated',
        resolved_vote_path: ['hardcoded-user-9', 'delegate-user-2'],
        final_delegatee_id: 'delegate-user-2'
      }
    },
    {
      id: 'hardcoded-10',
      title: 'Install solar panels on City Hall roof',
      description: 'Add renewable energy generation to municipal buildings, starting with City Hall.',
      created_by: 'hardcoded-user-10',
      created_at: '2025-01-14T16:15:00Z',
      updated_at: '2025-01-14T16:15:00Z',
      is_active: true,
      end_date: '2025-04-01T00:00:00Z',
      decision_type: 'level_b',
      your_vote_status: {
        status: 'voted',
        resolved_vote_path: ['hardcoded-user-10']
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
          <h1 className="text-2xl font-bold text-gov-primary">Community Ideas</h1>
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
          {/* Level A Section */}
          {levelAPolls.length > 0 && (activeFilter === 'all' || activeFilter === 'level_a') && (
            <LevelSection level="a" title="Long-Term Direction">
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {levelAPolls.map((poll, index) => (
                  <ProposalCard key={poll.id} poll={poll} index={index} />
                ))}
              </div>
            </LevelSection>
          )}

          {/* Level B Section */}
          {levelBPolls.length > 0 && (activeFilter === 'all' || activeFilter === 'level_b') && (
            <LevelSection level="b" title="Short-Term Decisions">
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {levelBPolls.map((poll, index) => (
                  <ProposalCard key={poll.id} poll={poll} index={index} />
                ))}
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
