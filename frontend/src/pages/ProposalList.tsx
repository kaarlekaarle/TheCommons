import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FileText, Plus } from 'lucide-react';
import { listPolls } from '../lib/api';
import type { Poll } from '../types';
import Button from '../components/ui/Button';
import Empty from '../components/ui/Empty';
import DebugRawData from '../components/ui/DebugRawData';
import { useToast } from '../components/ui/useToast';

export default function ProposalList() {
  const [polls, setPolls] = useState<Poll[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rawData, setRawData] = useState<any>(null);
  const { error: showError } = useToast();

  // Check if we should use hardcoded data
  const useHardcodedData = import.meta.env.VITE_USE_HARDCODED_DATA === 'true';

  // Hardcoded data for testing UI logic
  const hardcodedPolls: Poll[] = [
    {
      id: 'hardcoded-1',
      title: 'Community Garden Expansion',
      description: 'Proposal to expand the community garden with new plots and a greenhouse facility.',
      created_by: 'hardcoded-user-1',
      created_at: '2025-01-10T10:00:00Z',
      updated_at: '2025-01-10T10:00:00Z',
      is_active: true,
      end_date: '2025-02-15T00:00:00Z',
      your_vote_status: {
        status: 'none',
        resolved_vote_path: []
      }
    },
    {
      id: 'hardcoded-2',
      title: 'Neighborhood Watch Program',
      description: 'Establish a neighborhood watch program to improve community safety and security.',
      created_by: 'hardcoded-user-2',
      created_at: '2025-01-20T14:30:00Z',
      updated_at: '2025-01-20T14:30:00Z',
      is_active: false,
      end_date: '2025-03-01T00:00:00Z',
      your_vote_status: {
        status: 'voted',
        resolved_vote_path: ['hardcoded-user-2']
      }
    },
    {
      id: 'hardcoded-3',
      title: 'Local Business Support Initiative',
      description: 'Create a program to support local businesses through community partnerships and events.',
      created_by: 'hardcoded-user-3',
      created_at: '2025-01-05T09:15:00Z',
      updated_at: '2025-01-05T09:15:00Z',
      is_active: true,
      end_date: '2025-01-31T00:00:00Z',
      your_vote_status: {
        status: 'delegated',
        resolved_vote_path: ['hardcoded-user-3', 'delegate-user-1'],
        final_delegatee_id: 'delegate-user-1'
      }
    }
  ];

  const loadHardcodedData = () => {
    console.log('ProposalList: Loading hardcoded data...');
    setLoading(true);
    setError(null);
    
    // Simulate API delay
    setTimeout(() => {
      setPolls(hardcodedPolls);
      setRawData(hardcodedPolls);
      setLoading(false);
      console.log('ProposalList: Hardcoded data loaded successfully');
    }, 500);
  };

  useEffect(() => {
    console.log('ProposalList: Component mounted, fetching polls...');
    console.log('ProposalList: Token in localStorage:', !!localStorage.getItem('token'));
    console.log('ProposalList: Using hardcoded data:', useHardcodedData);
    
    if (useHardcodedData) {
      loadHardcodedData();
    } else {
      fetchPolls();
    }
  }, [useHardcodedData]);

  const fetchPolls = async () => {
    try {
      console.log('ProposalList: Starting to fetch polls...');
      setLoading(true);
      setError(null);
      const data = await listPolls();
      console.log('ProposalList: Successfully fetched polls:', data.length);
      setPolls(data);
      setRawData(data);
    } catch (err: unknown) {
      const error = err as { message: string; status?: number };
      console.error('ProposalList: Error fetching polls:', error);
      setError(error.message);
      showError('Failed to load proposals');
    } finally {
      setLoading(false);
    }
  };

  console.log('ProposalList: Rendering with loading:', loading, 'polls:', polls.length, 'error:', error);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <p className="text-red-500 mb-4">Error: {error}</p>
          <Button onClick={fetchPolls}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <FileText className="w-6 h-6 text-primary" />
          <h1 className="text-2xl font-bold text-white">Proposals</h1>
        </div>
        <Link to="/proposals/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Proposal
          </Button>
        </Link>
      </div>

      {polls.length === 0 ? (
        <Empty
          icon={<FileText className="w-8 h-8" />}
          title="No proposals yet"
          subtitle="Create the first one to get started."
          action={
            <Link to="/proposals/new">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Proposal
              </Button>
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {polls.map((poll, index) => (
            <motion.div
              key={poll.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
            >
              <Link
                to={`/proposals/${poll.id}`}
                className="block p-6 bg-surface border border-border rounded-lg hover:border-primary/50 transition-colors"
              >
                <h3 className="text-lg font-semibold text-white mb-2 line-clamp-2">
                  {poll.title}
                </h3>
                <p className="text-sm text-muted line-clamp-3 mb-4">
                  {poll.description}
                </p>
                <div className="flex items-center justify-between text-xs text-muted">
                  <span>Created {new Date(poll.created_at).toLocaleDateString()}</span>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
      
      <DebugRawData data={rawData} title="Raw Polls Data" />
    </div>
  );
}
