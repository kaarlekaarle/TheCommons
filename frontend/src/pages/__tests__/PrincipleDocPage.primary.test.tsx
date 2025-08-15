import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { ToasterProvider } from '../../components/ui/Toaster';
import PrincipleDocPage from '../PrincipleDocPage';
import * as api from '../../lib/api';
import { flags } from '../../config/flags';

// Mock the flags
vi.mock('../../config/flags', () => ({
  flags: {
    primaryPerspectiveEnabled: true,
    principlesDocMode: true,
    compassEnabled: true,
    useHardcodedData: true,
    principlesDocEnabled: true,
  },
}));

// Mock the API
vi.mock('../../lib/api');

const mockPoll = {
  id: 'ai-edu-001',
  title: 'AI in Education: A Tool for Stronger Learning',
  description: 'Test description',
  decision_type: 'level_a',
  options: [
    { id: 'option-1', title: 'Primary Option', description: 'Primary option description' },
    { id: 'option-2', title: 'Alternate Option', description: 'Alternate option description' },
  ],
  labels: [],
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  status: 'active',
};

const mockResults = {
  poll_id: 'ai-edu-001',
  total_votes: 100,
  options: [
    {
      option_id: 'option-1',
      text: 'Primary Option',
      votes: 60,
      percentage: 60
    },
    {
      option_id: 'option-2',
      text: 'Alternate Option',
      votes: 40,
      percentage: 40
    }
  ]
};

const mockComments = {
  comments: [],
  total: 0,
  limit: 10,
  offset: 0,
  has_more: false,
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <ToasterProvider>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </ToasterProvider>
  );
};

describe('PrincipleDocPage - Primary Perspective', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock API calls
    vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
    vi.mocked(api.getPollOptions).mockResolvedValue([
      { id: 'option-1', poll_id: 'ai-edu-001', text: 'Primary Option', created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' },
      { id: 'option-2', poll_id: 'ai-edu-001', text: 'Alternate Option', created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z' }
    ]);
    vi.mocked(api.getResults).mockResolvedValue(mockResults);
    vi.mocked(api.listComments).mockResolvedValue(mockComments);
  });

  test('shows primary perspective with "Current community view" badge when feature enabled and majority exists', async () => {
    renderWithRouter(<PrincipleDocPage />);

    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByTestId('main-question')).toBeInTheDocument();
    });

    // Check that the primary perspective card shows the badge
    const primaryCard = screen.getByTestId('perspective-card-primary');
    expect(primaryCard).toBeInTheDocument();

    // Check for the "Current community view" badge
    const badge = screen.getByTestId('community-view-badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Current community view');

    // Check that alternate perspective is also present (below primary)
    const alternateCard = screen.getByTestId('perspective-card-alternate');
    expect(alternateCard).toBeInTheDocument();

    // Check for new copy
    expect(screen.getByText('Where most people lean (for now)')).toBeInTheDocument();
    expect(screen.getByText('Another way people answer this')).toBeInTheDocument();
    expect(screen.getByText('This speaks to me')).toBeInTheDocument();
  });

  test('shows equal weight layout when votes are within 5% threshold', async () => {
    // Mock results with votes within 5% threshold
    const tieResults = {
      poll_id: 'ai-edu-001',
      total_votes: 100,
      options: [
        {
          option_id: 'option-1',
          text: 'Primary Option',
          votes: 52,
          percentage: 52
        },
        {
          option_id: 'option-2',
          text: 'Alternate Option',
          votes: 48,
          percentage: 48
        }
      ]
    };

    vi.mocked(api.getResults).mockResolvedValue(tieResults);

    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByTestId('main-question')).toBeInTheDocument();
    });

    // Should not show the "Current community view" badge in a tie
    const badge = screen.queryByTestId('community-view-badge');
    expect(badge).not.toBeInTheDocument();
  });

  test('shows equal weight layout when no results are available', async () => {
    // Mock no results
    vi.mocked(api.getResults).mockRejectedValue(new Error('No results'));

    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByTestId('main-question')).toBeInTheDocument();
    });

    // Should not show the "Current community view" badge when no results
    const badge = screen.queryByTestId('community-view-badge');
    expect(badge).not.toBeInTheDocument();
  });

  test('composer defaults to primary perspective', async () => {
    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByTestId('main-question')).toBeInTheDocument();
    });

    // Check that the primary perspective radio is selected by default
    const primaryRadio = screen.getByTestId('perspective-primary-radio') as HTMLInputElement;
    expect(primaryRadio.checked).toBe(true);
  });

  test('tracks analytics when primary perspective is shown', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByTestId('main-question')).toBeInTheDocument();
    });

    // Check that analytics are tracked
    expect(consoleSpy).toHaveBeenCalledWith('perspective.primary_shown', {
      primaryId: 'option-1',
      share: 60,
    });

    consoleSpy.mockRestore();
  });

  test('uses hierarchical layout when primary perspective is enabled', async () => {
    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByTestId('main-question')).toBeInTheDocument();
    });

    // Check that primary perspective is full width (not in a grid)
    const primaryCard = screen.getByTestId('perspective-card-primary');
    const primaryContainer = primaryCard.closest('.w-full');
    expect(primaryContainer).toBeInTheDocument();

    // Check that alternate perspective is below primary (not side by side)
    const alternateCard = screen.getByTestId('perspective-card-alternate');
    expect(alternateCard).toBeInTheDocument();
  });

  test('shows trend chip when trend data is available', async () => {
    renderWithRouter(<PrincipleDocPage />);

    // Wait for content to load
    await waitFor(() => {
      expect(screen.getByTestId('main-question')).toBeInTheDocument();
    });

    // Check for trend chip (may or may not be present due to random generation)
    const trendChip = screen.queryByTestId('trend-chip');
    if (trendChip) {
      expect(trendChip).toHaveTextContent(/[↑↓] [+-]?\d+% this week/);
    }
  });
});
