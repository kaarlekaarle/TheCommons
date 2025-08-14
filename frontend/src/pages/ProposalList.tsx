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

  // Hardcoded data for testing UI logic
  const hardcodedPolls: Poll[] = [
    {
      id: 'hardcoded-1',
      title: 'Install protected bike lanes on Washington Avenue from downtown to university district',
      description: 'Add dedicated, protected bicycle lanes along Washington Avenue to improve cyclist safety and encourage active transportation between downtown and the university.',
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
      title: 'Launch 18-month curbside composting pilot in four residential neighborhoods',
      description: 'Begin organic waste collection service in Downtown, Westside, Riverside, and Eastside neighborhoods to reduce landfill waste and create compost for city parks.',
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
      title: 'Complete Streets Policy',
      description: 'Design and maintain streets to safely accommodate all users including pedestrians, cyclists, transit riders, and motorists of all ages and abilities.',
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
      title: 'Extend public library hours to 9 PM on weekdays for six-month trial',
      description: 'Extend operating hours at the main library to better serve students, working families, and evening library users.',
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
      title: 'Public Records Transparency Policy',
      description: 'Make all public records and datasets available online unless specifically exempted by law, with clear processes for requesting information.',
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
      title: 'Plant 750 street trees along major transit corridors and in underserved neighborhoods',
      description: 'Add urban trees along bus routes and in neighborhoods with low tree canopy to improve air quality, provide shade, and enhance walkability.',
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
      title: 'Green Building Standards for Municipal Construction',
      description: 'Require all new municipal buildings and major renovations to meet LEED Silver certification or equivalent energy efficiency standards.',
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
      title: 'Inclusive Housing Development Policy',
      description: 'Ensure 20% of all new residential development includes affordable housing units or equivalent contributions to the housing trust fund.',
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
      title: 'Municipal Climate Action Plan',
      description: 'Reduce city government greenhouse gas emissions by 50% by 2030 and achieve carbon neutrality by 2040 through energy efficiency and renewable energy.',
      created_by: 'hardcoded-user-9',
      created_at: '2025-01-09T10:30:00Z',
      updated_at: '2025-01-09T10:30:00Z',
      is_active: true,
      end_date: '2025-03-05T00:00:00Z',
      decision_type: 'level_a',
      direction_choice: 'Climate & Sustainability',
      your_vote_status: {
        status: 'delegated',
        resolved_vote_path: ['hardcoded-user-9', 'delegate-user-2'],
        final_delegatee_id: 'delegate-user-2'
      }
    },
    {
      id: 'hardcoded-10',
      title: 'Retrofit lighting in all municipal buildings with energy-efficient LED systems',
      description: 'Replace existing lighting systems in 15 municipal buildings to reduce energy consumption by 40% and lower operating costs.',
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
