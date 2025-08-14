import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import type { Label, PopularLabel } from '../types';
import { getLabelsCached, getPopularLabelsCached } from '../lib/cache/labelsCache';
import { flags } from '../config/flags';
import LabelTile from '../components/ui/LabelTile';
import { Skeleton } from '../components/ui/Skeleton';

interface TopicsHubState {
  popularLabels: PopularLabel[];
  allLabels: Label[];
  isLoading: boolean;
  error: string | null;
}

const ITEMS_PER_PAGE = 24;

export default function TopicsHub() {
  const navigate = useNavigate();
  const [state, setState] = useState<TopicsHubState>({
    popularLabels: [],
    allLabels: [],
    isLoading: true,
    error: null
  });
  const [currentPage, setCurrentPage] = useState(1);

  const abortControllerRef = useRef<AbortController | null>(null);
  const isLoadingRef = useRef(false);

  const fetchData = useCallback(async () => {
    // Prevent multiple simultaneous fetches
    if (isLoadingRef.current) {
      return;
    }

    // Abort previous request if it exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();

    setState(prev => ({ ...prev, isLoading: true, error: null }));
    isLoadingRef.current = true;

    try {
      // Fetch popular labels first
      let popularData: PopularLabel[] = [];
      try {
        popularData = await getPopularLabelsCached(8);
      } catch (popularErr) {
        console.error('Failed to fetch popular labels:', popularErr);
        // Don't fail the entire page for popular labels
      }

      // Fetch all labels (with cache)
      let allLabelsData: Label[] = [];
      try {
        allLabelsData = await getLabelsCached();
      } catch (allLabelsErr) {
        console.error('Failed to fetch all labels:', allLabelsErr);
        throw new Error('Failed to load topics');
      }

      setState({
        popularLabels: popularData,
        allLabels: allLabelsData,
        isLoading: false,
        error: null
      });
    } catch (err) {
      if (err && typeof err === 'object' && 'name' in err && err.name === 'AbortError') {
        return; // Request was aborted
      }
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Failed to load topics'
      }));
    } finally {
      isLoadingRef.current = false;
    }
  }, []);

  useEffect(() => {
    if (flags.labelsEnabled) {
      fetchData();
    }
  }, [fetchData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleLabelClick = useCallback((slug: string) => {
    navigate(`/t/${slug}`);
  }, [navigate]);

  // Pagination logic
  const totalPages = Math.ceil(state.allLabels.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentLabels = state.allLabels.slice(startIndex, endIndex);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    // Scroll to top of the All Topics section
    const allTopicsSection = document.getElementById('all-topics');
    if (allTopicsSection) {
      allTopicsSection.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  if (!flags.labelsEnabled) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Topics Feature Disabled</h1>
          <p className="text-gray-600">The topics feature is currently disabled.</p>
        </div>
      </div>
    );
  }

  if (state.isLoading) {
    return (
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        
        <div className="mb-12">
          <Skeleton className="h-6 w-32 mb-4" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" data-testid="skeleton-grid">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
        
        <div id="all-topics">
          <Skeleton className="h-6 w-32 mb-4" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" data-testid="skeleton-grid">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        </div>
      </main>
    );
  }

  if (state.error) {
    return (
      <main className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Topics</h1>
          <p className="text-gray-600 mb-4">{state.error}</p>
          <button
            onClick={fetchData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Try Again
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="container mx-auto px-4 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 
          id="topics-heading"
          className="text-3xl font-bold text-gray-900 mb-2"
        >
          Browse Topics
        </h1>
        <p 
          id="topics-description"
          className="text-gray-600"
          aria-describedby="topics-heading"
        >
          Follow what matters to you and see related principles and actions.
        </p>
      </div>

      {/* Popular Topics Section */}
      <div className="mb-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Popular Topics</h2>
        {state.popularLabels.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {state.popularLabels.map((label, index) => (
              <motion.div
                key={label.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <LabelTile
                  label={{
                    id: label.id,
                    name: label.name,
                    slug: label.slug,
                    is_active: true,
                    created_at: '',
                    updated_at: ''
                  }}
                  count={label.poll_count}
                  onClick={handleLabelClick}
                />
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-600 mb-2">No popular topics yet.</p>
            <a 
              href="#all-topics" 
              className="text-blue-600 hover:text-blue-800 underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Browse all topics
            </a>
          </div>
        )}
      </div>

      {/* All Topics Section */}
      <div id="all-topics">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          All Topics ({state.allLabels.length})
        </h2>
        
        {currentLabels.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600">No topics available</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {currentLabels.map((label, index) => (
              <motion.div
                key={label.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.02 }}
              >
                <LabelTile
                  label={label}
                  onClick={handleLabelClick}
                />
              </motion.div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && currentLabels.length > 0 && (
          <div className="mt-8 flex justify-center">
            <nav className="flex items-center space-x-2" role="navigation" aria-label="Topics pagination">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Previous
              </button>
              
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                <button
                  key={page}
                  onClick={() => handlePageChange(page)}
                  className={`px-3 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    page === currentPage
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              ))}
              
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Next
              </button>
            </nav>
          </div>
        )}
      </div>
    </main>
  );
}
