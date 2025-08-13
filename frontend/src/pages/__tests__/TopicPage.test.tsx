import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TopicPage from '../TopicPage';
import * as api from '../../lib/api';

// Mock the API functions
vi.mock('../../lib/api');
vi.mock('../../config/flags', () => ({
  flags: {
    labelsEnabled: true,
  },
}));

vi.mock('../../components/ui/useToast', () => ({
  useToast: () => ({
    error: vi.fn(),
    success: vi.fn(),
  }),
}));

const mockOverview = {
  label: {
    id: 'label-1',
    name: 'Mobility',
    slug: 'mobility',
  },
  counts: {
    level_a: 3,
    level_b: 7,
    level_c: 2,
    total: 12,
  },
  page: {
    page: 1,
    per_page: 12,
    total: 12,
    total_pages: 1,
  },
  items: [
    {
      id: 'poll-1',
      title: 'Recent Poll 1',
      decision_type: 'level_b',
      created_at: '2024-01-01T00:00:00Z',
      labels: [{ name: 'Mobility', slug: 'mobility' }],
    },
    {
      id: 'poll-2',
      title: 'Recent Poll 2',
      decision_type: 'level_a',
      created_at: '2024-01-02T00:00:00Z',
      labels: [{ name: 'Mobility', slug: 'mobility' }],
    },
  ],
  delegation_summary: {
    label_delegate: null,
    global_delegate: {
      id: 'user-1',
      username: 'alex',
      email: 'alex@example.com',
    },
  },
};

const mockPopularLabels = [
  {
    id: 'label-1',
    name: 'Mobility',
    slug: 'mobility',
    poll_count: 10,
  },
  {
    id: 'label-2',
    name: 'Environment',
    slug: 'environment',
    poll_count: 8,
  },
];

const mockNavigate = vi.fn();
const mockSetSearchParams = vi.fn();

const renderTopicPage = () => {
  return render(
    <BrowserRouter>
      <TopicPage />
    </BrowserRouter>
  );
};

describe('TopicPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock the useParams hook
    vi.mock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom');
      return {
        ...actual,
        useParams: () => ({ slug: 'mobility' }),
        useNavigate: () => mockNavigate,
        useSearchParams: () => [
          new URLSearchParams('tab=all&page=1&per_page=12&sort=newest'),
          mockSetSearchParams
        ],
      };
    });
  });

  it('renders loading state initially', () => {
    vi.mocked(api.getLabelOverview).mockImplementation(() => new Promise(() => {}));
    vi.mocked(api.getPopularLabels).mockImplementation(() => new Promise(() => {}));
    
    renderTopicPage();
    
    // Check for skeleton elements
    expect(screen.getByTestId('skeleton-grid')).toBeInTheDocument();
  });

  it('renders topic overview when data loads successfully', async () => {
    vi.mocked(api.getLabelOverview).mockResolvedValue(mockOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue(mockPopularLabels);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Mobility' })).toBeInTheDocument();
    });
    
    expect(screen.getByText('3')).toBeInTheDocument(); // Principles count
    expect(screen.getByText('7')).toBeInTheDocument(); // Actions count
    expect(screen.getByText('2')).toBeInTheDocument(); // Problems count
    expect(screen.getByText('12')).toBeInTheDocument(); // Total count
  });

  it('switches between tabs correctly', async () => {
    vi.mocked(api.getLabelOverview).mockResolvedValue(mockOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue(mockPopularLabels);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Mobility' })).toBeInTheDocument();
    });
    
    // Check that All tab is active by default
    const allTab = screen.getByRole('button', { name: 'All' });
    expect(allTab).toHaveClass('bg-primary-600');
    
    // Click on Principles tab
    const principlesTab = screen.getByRole('button', { name: 'principles' });
    fireEvent.click(principlesTab);
    
    // Verify setSearchParams was called with the new tab parameter
    expect(mockSetSearchParams).toHaveBeenCalledWith(
      expect.any(URLSearchParams)
    );
    
    // Check that the URLSearchParams contains the expected values
    const callArgs = mockSetSearchParams.mock.calls[0][0];
    expect(callArgs.get('tab')).toBe('principles');
    expect(callArgs.get('page')).toBe('1');
    expect(callArgs.get('per_page')).toBe('12');
    expect(callArgs.get('sort')).toBe('newest');
  });

  it('changes sort order correctly', async () => {
    vi.mocked(api.getLabelOverview).mockResolvedValue(mockOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue(mockPopularLabels);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Mobility' })).toBeInTheDocument();
    });
    
    // Change sort order
    const sortSelect = screen.getByLabelText('Sort by:');
    fireEvent.change(sortSelect, { target: { value: 'oldest' } });
    
    // Verify setSearchParams was called with the new sort parameter
    expect(mockSetSearchParams).toHaveBeenCalledWith(
      expect.any(URLSearchParams)
    );
    
    // Check that the URLSearchParams contains the expected values
    const callArgs = mockSetSearchParams.mock.calls[0][0];
    expect(callArgs.get('tab')).toBe('all');
    expect(callArgs.get('page')).toBe('1');
    expect(callArgs.get('per_page')).toBe('12');
    expect(callArgs.get('sort')).toBe('oldest');
  });

  it('shows pagination when there are multiple pages', async () => {
    const multiPageOverview = {
      ...mockOverview,
      page: {
        page: 1,
        per_page: 12,
        total: 25,
        total_pages: 3,
      },
    };
    
    vi.mocked(api.getLabelOverview).mockResolvedValue(multiPageOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue(mockPopularLabels);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByText('Showing 1 to 12 of 25 results')).toBeInTheDocument();
    });
    
    expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument();
  });

  it('shows delegation information when available', async () => {
    vi.mocked(api.getLabelOverview).mockResolvedValue(mockOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue(mockPopularLabels);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByText('Your Delegation')).toBeInTheDocument();
    });
    
    expect(screen.getByText('alex')).toBeInTheDocument(); // Global delegate
    expect(screen.getByText('Not set')).toBeInTheDocument(); // Topic delegate
  });

  it('shows popular topics section', async () => {
    vi.mocked(api.getLabelOverview).mockResolvedValue(mockOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue(mockPopularLabels);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByText('Popular Topics')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Environment')).toBeInTheDocument();
  });

  it('shows empty state when no items in current tab', async () => {
    const emptyOverview = {
      ...mockOverview,
      items: [],
      page: {
        page: 1,
        per_page: 12,
        total: 0,
        total_pages: 0,
      },
    };
    
    vi.mocked(api.getLabelOverview).mockResolvedValue(emptyOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue([]);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByText('No all yet')).toBeInTheDocument();
    });
  });

  it('handles error state gracefully', async () => {
    vi.mocked(api.getLabelOverview).mockRejectedValue(new Error('Failed to load'));
    vi.mocked(api.getPopularLabels).mockResolvedValue([]);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByText('Topic not found')).toBeInTheDocument();
    });
  });

  it('navigates to topic page when label chip is clicked', async () => {
    vi.mocked(api.getLabelOverview).mockResolvedValue(mockOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue(mockPopularLabels);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Mobility' })).toBeInTheDocument();
    });
    
    // Find and click a label chip in the poll items (not the header)
    const pollItems = screen.getAllByText('Recent Poll 1');
    expect(pollItems.length).toBeGreaterThan(0);
    
    // Find the label chip within the poll item
    const pollItem = pollItems[0].closest('.bg-gray-800');
    const labelChip = pollItem?.querySelector('[title="Mobility"]');
    expect(labelChip).toBeInTheDocument();
    fireEvent.click(labelChip!);
    
    // Verify navigation was called
    expect(mockNavigate).toHaveBeenCalledWith('/t/mobility?tab=all&page=1&per_page=12&sort=newest');
  });

  it('updates document title for SEO', async () => {
    vi.mocked(api.getLabelOverview).mockResolvedValue(mockOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue(mockPopularLabels);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(document.title).toBe('Mobility · Topics · The Commons');
    });
  });

  it('shows breadcrumbs navigation', async () => {
    vi.mocked(api.getLabelOverview).mockResolvedValue(mockOverview);
    vi.mocked(api.getPopularLabels).mockResolvedValue(mockPopularLabels);
    
    renderTopicPage();
    
    await waitFor(() => {
      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Topics')).toBeInTheDocument();
      // Check for Mobility in the breadcrumb specifically
      const breadcrumbItems = screen.getAllByText('Mobility');
      expect(breadcrumbItems.length).toBeGreaterThan(0);
    });
  });
});
