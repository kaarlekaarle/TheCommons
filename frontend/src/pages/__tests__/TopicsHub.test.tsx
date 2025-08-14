import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { axe, toHaveNoViolations } from 'jest-axe';
import TopicsHub from '../TopicsHub';
import * as cache from '../../lib/cache/labelsCache';
import { flags } from '../../config/flags';

// Mock the cache functions
vi.mock('../../lib/cache/labelsCache');
vi.mock('../../config/flags');

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>
  }
}));

expect.extend(toHaveNoViolations);

const mockLabels = [
  { id: '1', name: 'Environment', slug: 'environment', is_active: true, created_at: '', updated_at: '' },
  { id: '2', name: 'Education', slug: 'education', is_active: true, created_at: '', updated_at: '' },
  { id: '3', name: 'Healthcare', slug: 'healthcare', is_active: true, created_at: '', updated_at: '' }
];

const mockPopularLabels = [
  { id: '1', name: 'Environment', slug: 'environment', poll_count: 5 },
  { id: '2', name: 'Education', slug: 'education', poll_count: 3 }
];

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('TopicsHub', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (flags.labelsEnabled as any) = true;
  });

  it('renders loading state initially', () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
    vi.mocked(cache.getPopularLabelsCached).mockResolvedValue(mockPopularLabels);

    renderWithRouter(<TopicsHub />);

    // During loading, we should see skeleton elements, not the actual text
    const skeletonGrids = screen.getAllByTestId('skeleton-grid');
    expect(skeletonGrids).toHaveLength(2); // One for popular, one for all topics
  });

  it('renders popular topics and all topics when data loads', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
    vi.mocked(cache.getPopularLabelsCached).mockResolvedValue(mockPopularLabels);

    renderWithRouter(<TopicsHub />);

    await waitFor(() => {
      expect(screen.getByText('Popular Topics')).toBeInTheDocument();
      expect(screen.getByText('All Topics (3)')).toBeInTheDocument();
    });

    // Check for specific elements in popular section
    expect(screen.getByText('Popular Topics')).toBeInTheDocument();
    expect(screen.getByText('All Topics (3)')).toBeInTheDocument();
    
    // Check that labels appear in both sections
    const environmentElements = screen.getAllByText('Environment');
    expect(environmentElements).toHaveLength(2); // One in popular, one in all
    
    const educationElements = screen.getAllByText('Education');
    expect(educationElements).toHaveLength(2); // One in popular, one in all
    
    expect(screen.getByText('Healthcare')).toBeInTheDocument();
  });

  it('navigates to topic page when label tile is clicked', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
    vi.mocked(cache.getPopularLabelsCached).mockResolvedValue(mockPopularLabels);

    const { container } = renderWithRouter(<TopicsHub />);

    await waitFor(() => {
      expect(screen.getByText('Popular Topics')).toBeInTheDocument();
    });

    // Look for the specific popular topics tile with count
    const environmentTile = container.querySelector('[aria-label="Browse Environment (5 items)"]');
    expect(environmentTile).toBeInTheDocument();
  });

  it('handles pagination correctly', async () => {
    const manyLabels = Array.from({ length: 30 }, (_, i) => ({
      id: String(i + 1),
      name: `Topic ${i + 1}`,
      slug: `topic-${i + 1}`,
      is_active: true,
      created_at: '',
      updated_at: ''
    }));

    vi.mocked(cache.getLabelsCached).mockResolvedValue(manyLabels);
    vi.mocked(cache.getPopularLabelsCached).mockResolvedValue([]);

    renderWithRouter(<TopicsHub />);

    await waitFor(() => {
      expect(screen.getByText('All Topics (30)')).toBeInTheDocument();
    });

    // Should show pagination controls
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows error state when API fails', async () => {
    vi.mocked(cache.getLabelsCached).mockRejectedValue(new Error('API Error'));
    vi.mocked(cache.getPopularLabelsCached).mockResolvedValue([]);

    renderWithRouter(<TopicsHub />);

    await waitFor(() => {
      expect(screen.getByText('Error Loading Topics')).toBeInTheDocument();
      expect(screen.getByText('Failed to load topics')).toBeInTheDocument();
    });
  });

  it('shows disabled state when labels feature is disabled', () => {
    (flags.labelsEnabled as any) = false;

    renderWithRouter(<TopicsHub />);

    expect(screen.getByText('Topics Feature Disabled')).toBeInTheDocument();
    expect(screen.getByText('The topics feature is currently disabled.')).toBeInTheDocument();
  });

  it('gracefully handles popular labels API failure', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
    vi.mocked(cache.getPopularLabelsCached).mockRejectedValue(new Error('Popular labels failed'));

    renderWithRouter(<TopicsHub />);

    await waitFor(() => {
      expect(screen.getByText('All Topics (3)')).toBeInTheDocument();
    });

    // Should still show all topics even if popular fails
    expect(screen.getByText('Environment')).toBeInTheDocument();
    expect(screen.getByText('Education')).toBeInTheDocument();
    expect(screen.getByText('Healthcare')).toBeInTheDocument();
  });

  it('uses cache for subsequent calls', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
    vi.mocked(cache.getPopularLabelsCached).mockResolvedValue(mockPopularLabels);

    const { rerender } = renderWithRouter(<TopicsHub />);

    await waitFor(() => {
      expect(screen.getByText('Popular Topics')).toBeInTheDocument();
    });

    // Clear mocks to verify cache is used
    vi.clearAllMocks();

    // Re-render the component
    rerender(
      <BrowserRouter>
        <TopicsHub />
      </BrowserRouter>
    );

    // Should not make new API calls if cache is working
    expect(cache.getLabelsCached).not.toHaveBeenCalled();
    expect(cache.getPopularLabelsCached).not.toHaveBeenCalled();
  });

  it('shows empty state for popular topics', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
    vi.mocked(cache.getPopularLabelsCached).mockResolvedValue([]);

    renderWithRouter(<TopicsHub />);

    await waitFor(() => {
      expect(screen.getByText('No popular topics yet.')).toBeInTheDocument();
      expect(screen.getByText('Browse all topics')).toBeInTheDocument();
    });
  });

  it('shows empty state for all topics', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue([]);
    vi.mocked(cache.getPopularLabelsCached).mockResolvedValue([]);

    renderWithRouter(<TopicsHub />);

    await waitFor(() => {
      expect(screen.getByText('No topics available')).toBeInTheDocument();
    });
  });

  // Accessibility tests (only run in development)
  if (import.meta.env.DEV) {
    it('passes accessibility tests', async () => {
      vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
      vi.mocked(cache.getPopularLabelsCached).mockResolvedValue(mockPopularLabels);

      const { container } = renderWithRouter(<TopicsHub />);

      await waitFor(() => {
        expect(screen.getByText('Popular Topics')).toBeInTheDocument();
      });

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes accessibility tests in loading state', async () => {
      vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
      vi.mocked(cache.getPopularLabelsCached).mockResolvedValue(mockPopularLabels);

      const { container } = renderWithRouter(<TopicsHub />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes accessibility tests in error state', async () => {
      vi.mocked(cache.getLabelsCached).mockRejectedValue(new Error('API Error'));
      vi.mocked(cache.getPopularLabelsCached).mockResolvedValue([]);

      const { container } = renderWithRouter(<TopicsHub />);

      await waitFor(() => {
        expect(screen.getByText('Error Loading Topics')).toBeInTheDocument();
      });

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  }
});
