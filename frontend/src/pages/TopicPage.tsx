import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, 
  Users, 
  Target, 
  Compass, 
  TrendingUp,
  ExternalLink,
  UserCheck,
  UserX,
  AlertTriangle,
  ChevronDown
} from 'lucide-react';
import { getLabelOverview, getPopularLabels } from '../lib/api';
import type { LabelOverview, PopularLabel, PollSummary } from '../types';
import Button from '../components/ui/Button';
import LabelChip from '../components/ui/LabelChip';
import { useToast } from '../components/ui/useToast';
import Empty from '../components/ui/Empty';
import { SkeletonGrid, Skeleton } from '../components/ui/Skeleton';
import { Pagination } from '../components/ui/Pagination';

type TabType = 'all' | 'principles' | 'actions';
type SortType = 'newest' | 'oldest';

export default function TopicPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [overview, setOverview] = useState<LabelOverview | null>(null);
  const [popularLabels, setPopularLabels] = useState<PopularLabel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { error: showError } = useToast();

  // URL state management
  const activeTab = (searchParams.get('tab') as TabType) || 'all';
  const currentPage = parseInt(searchParams.get('page') || '1');
  const perPage = parseInt(searchParams.get('per_page') || '12');
  const sortOrder = (searchParams.get('sort') as SortType) || 'newest';

  // Update document title and meta description for SEO
  useEffect(() => {
    if (overview?.label) {
      document.title = `${overview.label.name} · Topics · The Commons`;
      
      // Update meta description
      const metaDescription = document.querySelector('meta[name="description"]');
      if (metaDescription) {
        metaDescription.setAttribute('content', `${overview.label.name} topic — principles and actions for community decision-making`);
      }
    }
  }, [overview]);

  // Fetch data when URL parameters change
  useEffect(() => {
    if (!slug) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const [overviewData, popularData] = await Promise.all([
          getLabelOverview(slug, {
            tab: activeTab,
            page: currentPage,
            per_page: perPage,
            sort: sortOrder
          }),
          getPopularLabels(8)
        ]);
        
        setOverview(overviewData);
        setPopularLabels(popularData);
      } catch (err: unknown) {
        console.error('Failed to fetch topic data:', err);
        let errorMessage = 'Failed to load topic data';
        
        if (err && typeof err === 'object') {
          if ('message' in err && typeof err.message === 'string') {
            errorMessage = err.message;
          } else if ('detail' in err && typeof err.detail === 'string') {
            errorMessage = err.detail;
          } else if ('status' in err && typeof err.status === 'number') {
            errorMessage = `Error ${err.status}: Failed to load topic data`;
          }
        }
        
        setError(errorMessage);
        showError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [slug, activeTab, currentPage, perPage, sortOrder, showError]);

  const handleLabelClick = (labelSlug: string) => {
    // Preserve existing query params except page (reset to 1)
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', '1');
    navigate(`/t/${labelSlug}?${newParams.toString()}`);
  };

  const handleTabChange = (tab: TabType) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('tab', tab);
    newParams.set('page', '1'); // Reset to page 1 when changing tabs
    setSearchParams(newParams);
  };

  const handleSortChange = (sort: SortType) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('sort', sort);
    setSearchParams(newParams);
  };

  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', page.toString());
    setSearchParams(newParams);
  };

  const getTabTitle = () => {
    switch (activeTab) {
      case 'principles':
        return 'Principles';
      case 'actions':
        return 'Actions';
      default:
        return 'All';
    }
  };

  const getTabCount = () => {
    if (!overview) return 0;
    
    switch (activeTab) {
      case 'principles':
        return overview.counts.level_a;
      case 'actions':
        return overview.counts.level_b;
      default:
        return overview.counts.total;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        {/* Breadcrumbs skeleton */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 w-32" />
          </div>
          
          <div className="flex items-center gap-3 mb-4">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-8 w-20 rounded-full" />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-gray-800 rounded-lg p-4">
                <Skeleton className="h-4 w-16 mb-2" />
                <Skeleton className="h-6 w-8" />
              </div>
            ))}
          </div>
        </div>

        {/* Tabs skeleton */}
        <div className="flex gap-4 mb-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-24" />
          ))}
        </div>

        {/* Content skeleton */}
        <SkeletonGrid count={12} />
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Empty
          icon={<Target className="w-8 h-8" />}
          title="Topic not found"
          subtitle={error || "The topic you're looking for doesn't exist."}
        />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Breadcrumbs */}
      <nav className="mb-8" aria-label="Breadcrumb">
        <ol className="flex items-center gap-2 text-sm text-gray-400">
          <li>
            <Link to="/dashboard" className="hover:text-white transition-colors">
              Home
            </Link>
          </li>
          <li>
            <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
          </li>
          <li>
            <Link to="/dashboard" className="hover:text-white transition-colors">
              Topics
            </Link>
          </li>
          <li>
            <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
          </li>
          <li className="text-white font-medium">
            {overview.label.name}
          </li>
        </ol>
      </nav>
      
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <h1 className="text-3xl font-bold text-white">{overview.label.name}</h1>
          <LabelChip 
            label={{ 
              id: overview.label.id, 
              name: overview.label.name, 
              slug: overview.label.slug,
              is_active: true,
              created_at: '',
              updated_at: ''
            }} 
            size="lg"
          />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-400 mb-2">
              <Compass className="w-4 h-4" />
              <span className="text-sm">Principles</span>
            </div>
            <div className="text-2xl font-bold text-white">{overview.counts.level_a}</div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-400 mb-2">
              <Target className="w-4 h-4" />
              <span className="text-sm">Actions</span>
            </div>
            <div className="text-2xl font-bold text-white">{overview.counts.level_b}</div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-400 mb-2">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm">Problems</span>
            </div>
            <div className="text-2xl font-bold text-white">{overview.counts.level_c}</div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-400 mb-2">
              <TrendingUp className="w-4 h-4" />
              <span className="text-sm">Total</span>
            </div>
            <div className="text-2xl font-bold text-white">{overview.counts.total}</div>
          </div>
        </div>

        {/* Delegation Summary */}
        {overview.delegation_summary && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Your Delegation</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 text-gray-400">
                  <UserCheck className="w-4 h-4" />
                  <span className="text-sm">Topic Delegate</span>
                </div>
                <div className="text-white">
                  {overview.delegation_summary.label_delegate ? (
                    overview.delegation_summary.label_delegate.username
                  ) : (
                    <span className="text-gray-500">Not set</span>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 text-gray-400">
                  <Users className="w-4 h-4" />
                  <span className="text-sm">Global Delegate</span>
                </div>
                <div className="text-white">
                  {overview.delegation_summary.global_delegate ? (
                    overview.delegation_summary.global_delegate.username
                  ) : (
                    <span className="text-gray-500">Not set</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex gap-1">
          {(['all', 'principles', 'actions'] as const).map((tab) => (
            <Button
              key={tab}
              variant={activeTab === tab ? "primary" : "secondary"}
              size="sm"
              onClick={() => handleTabChange(tab)}
              className="capitalize"
            >
              {tab === 'all' ? 'All' : tab}
            </Button>
          ))}
        </div>
        
        <div className="flex items-center gap-2">
          <label htmlFor="sort-select" className="text-sm text-gray-400">
            Sort by:
          </label>
          <select
            id="sort-select"
            value={sortOrder}
            onChange={(e) => handleSortChange(e.target.value as SortType)}
            className="bg-gray-800 border border-gray-600 rounded px-3 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
          </select>
        </div>
      </div>

      {/* Content */}
      <div className="mb-8">
        {overview.items.length === 0 ? (
          <Empty
            icon={<Target className="w-8 h-8" />}
            title={`No ${getTabTitle().toLowerCase()} yet`}
            subtitle={`There are no ${getTabTitle().toLowerCase()} for this topic yet.`}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {overview.items.map((poll) => (
              <motion.div
                key={poll.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white line-clamp-2">
                    {poll.title}
                  </h3>
                  <Link
                    to={`/proposals/${poll.id}`}
                    className="text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Link>
                </div>
                
                <div className="flex items-center gap-2 mb-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    poll.decision_type === 'level_a' ? 'bg-blue-900 text-blue-200' :
                    poll.decision_type === 'level_b' ? 'bg-green-900 text-green-200' :
                    'bg-red-900 text-red-200'
                  }`}>
                    {poll.decision_type === 'level_a' ? 'Principle' :
                     poll.decision_type === 'level_b' ? 'Action' : 'Problem'}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(poll.created_at).toLocaleDateString()}
                  </span>
                </div>
                
                <div className="flex flex-wrap gap-1">
                  {poll.labels.map((label) => (
                    <LabelChip
                      key={`poll-${poll.id}-label-${label.slug}`}
                      label={{
                        id: '',
                        name: label.name,
                        slug: label.slug,
                        is_active: true,
                        created_at: '',
                        updated_at: ''
                      }}
                      size="sm"
                      onClick={() => handleLabelClick(label.slug)}
                    />
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {overview.page.total_pages > 1 && (
        <Pagination
          currentPage={overview.page.page}
          totalPages={overview.page.total_pages}
          totalItems={overview.page.total}
          perPage={overview.page.per_page}
          onPageChange={handlePageChange}
          className="mt-8"
        />
      )}

      {/* Popular Topics */}
      {popularLabels.length > 0 && (
        <div className="mt-12">
          <h2 className="text-xl font-semibold text-white mb-4">Popular Topics</h2>
          <div className="flex flex-wrap gap-2">
            {popularLabels.map((label) => (
              <LabelChip
                key={`popular-label-${label.id}`}
                label={{
                  id: label.id,
                  name: label.name,
                  slug: label.slug,
                  is_active: true,
                  created_at: '',
                  updated_at: ''
                }}
                onClick={() => handleLabelClick(label.slug)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
