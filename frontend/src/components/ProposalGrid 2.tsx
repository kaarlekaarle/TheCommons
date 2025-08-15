import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { FileText, Plus, Tag, X } from 'lucide-react';
import { listPolls } from '../lib/api';
import type { Poll, DecisionType } from '../types';
import Button from './ui/Button';
import Empty from './ui/Empty';
import { useToast } from './ui/useToast';
import ProposalCard from './ProposalCard';
import LabelFilterBar from './ui/LabelFilterBar';
import { flags } from '../config/flags';

interface ProposalGridProps {
  title: string;
  decisionType: DecisionType;
  emptyTitle: string;
  emptySubtitle: string;
  ctaLabel: string;
  pageDescription?: string;
}

export default function ProposalGrid({
  title,
  decisionType,
  emptyTitle,
  emptySubtitle,
  ctaLabel,
  pageDescription
}: ProposalGridProps) {
  const [polls, setPolls] = useState<Poll[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { error: showError } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  // const navigate = useNavigate(); // Unused for now

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
      // Filter hardcoded data by decision type
      const filteredPolls = hardcodedPolls.filter(poll => poll.decision_type === decisionType);
      setPolls(filteredPolls);
      setLoading(false);
    } else {
      fetchPolls();
    }
  }, [useHardcodedData, decisionType, searchParams]);

    const fetchPolls = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get label filter from URL params
      const labelFilter = searchParams.get('label');

      const fetchedPolls = await listPolls({
        decision_type: decisionType,
        label: labelFilter || undefined
      });
      setPolls(fetchedPolls);
    } catch (err: unknown) {
      const error = err as { message: string };
      console.error('Failed to load polls:', error.message);
      setError(error.message);
      showError(`Failed to load ${decisionType === 'level_a' ? 'principles' : 'actions'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLabelFilterChange = (slug: string | null) => {
    if (slug) {
      setSearchParams({ label: slug });
    } else {
      setSearchParams({});
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-neutral-600">Loading {decisionType === 'level_a' ? 'principles' : 'actions'}...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <Button onClick={fetchPolls}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-md flex items-center justify-center ${
            decisionType === 'level_a' ? 'bg-primary-600' : 'bg-success-600'
          }`}>
            <FileText className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-neutral-900">{title}</h1>
            {pageDescription && (
              <p className="text-lg text-neutral-700 max-w-prose mt-1">{pageDescription}</p>
            )}
            {/* Label filter indicator */}
            {flags.labelsEnabled && searchParams.get('label') && (
              <div className="flex items-center gap-2 mt-2">
                <Tag className="w-4 h-4 text-blue-600" />
                <span className="text-sm text-blue-600 font-medium">
                  Filtered by: {searchParams.get('label')}
                </span>
                <Link
                  to={window.location.pathname}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <X className="w-4 h-4" />
                </Link>
              </div>
            )}
          </div>
        </div>
        <Link to={`/proposals/new?type=${decisionType}`}>
          <Button variant={decisionType === 'level_a' ? 'primary' : 'success'}>
            <Plus className="w-4 h-4 mr-2" />
            {ctaLabel}
          </Button>
        </Link>
      </div>

      {/* Label Filter Bar */}
      {flags.labelsEnabled && (
        <div className="mb-6">
          <LabelFilterBar
            activeSlug={searchParams.get('label') || undefined}
            onChange={handleLabelFilterChange}
          />
        </div>
      )}

      {polls.length === 0 ? (
        <Empty
          icon={<FileText className="w-8 h-8" />}
          title={emptyTitle}
          subtitle={emptySubtitle}
          action={
            <Link to={`/proposals/new?type=${decisionType}`}>
              <Button variant="primary">
                <Plus className="w-4 h-4 mr-2" />
                {ctaLabel}
              </Button>
            </Link>
          }
        />
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {polls.map((poll, index) => (
            <ProposalCard key={poll.id} poll={poll} index={index} />
          ))}
        </div>
      )}
    </div>
  );
}
