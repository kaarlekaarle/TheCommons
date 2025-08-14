import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import CompassPage, { type RetryScheduler } from '../CompassPage';
import { getPoll, getPollOptions, getMyVoteForPoll, getResults, listComments } from '../../lib/api';
import { ToasterProvider } from '../../components/ui/Toaster';

// Test scheduler that resolves immediately
const immediateScheduler: RetryScheduler = {
  wait: () => Promise.resolve()
};

// Mock the API
vi.mock('../../lib/api', () => ({
  getPoll: vi.fn(),
  getPollOptions: vi.fn(),
  getMyVoteForPoll: vi.fn(),
  getResults: vi.fn(),
  listComments: vi.fn(),
}));

// Mock the flags
vi.mock('../../config/flags', () => ({
  flags: {
    compassEnabled: true,
    labelsEnabled: true,
  },
}));

// Mock the copy
vi.mock('../../copy/compass', () => ({
  compassCopy: {
    framing: "A long-term compass that guides related community decisions.",
    directionsTitle: "Choose a direction to align with (coming soon)",
    reasoningTitle: "Community reasoning",
    reasoningCta: "Take part in the conversation",
    contextTitle: "Background",
    share: "Share",
    errorTitle: "Compass unavailable",
    errorBody: "We couldn't load this compass right now.",
    retry: "Try again",
    alignCta: "Align with this direction",
    alignedWith: "You're aligned with",
    changeAlignment: "Change alignment",
    tallyTitle: "Community alignment (so far)",
    reasoningLabel: "Share why you lean this way",
    reasoningHelper: "Short essay. 240–1000 characters.",
    postReasoning: "Post reasoning",
    posting: "Posting…",
    postSuccess: "Thank you for sharing your reasoning!",
    loadMore: "Load more"
  },
}));

const mockNavigate = vi.fn();

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: 'test-id' }),
    useNavigate: () => mockNavigate,
  };
});

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <ToasterProvider>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </ToasterProvider>
  );
};

describe('CompassPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders compass page for level_a poll', async () => {
    // Mock successful API responses
    vi.mocked(getPoll).mockResolvedValue({
      id: 'test-id',
      title: 'Test Compass',
      description: 'Test description',
      decision_type: 'level_a' as const,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      created_by: 'user-1',
      is_active: true,
      labels: []
    });

    vi.mocked(getPollOptions).mockResolvedValue([
      { id: 'option-1', poll_id: 'test-id', text: 'Direction A', created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
      { id: 'option-2', poll_id: 'test-id', text: 'Direction B', created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' }
    ]);

    vi.mocked(getMyVoteForPoll).mockResolvedValue(null);
    vi.mocked(getResults).mockResolvedValue({
      poll_id: 'test-id',
      total_votes: 0,
      options: []
    });
    vi.mocked(listComments).mockResolvedValue({
      comments: [],
      total: 0,
      limit: 10,
      offset: 0,
      has_more: false
    });

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Compass')).toBeInTheDocument();
    });

    // Check that direction cards are rendered
    expect(screen.getByTestId('direction-title-option-1')).toBeInTheDocument();
    expect(screen.getByTestId('direction-title-option-2')).toBeInTheDocument();

    // Check that framing text is rendered
    expect(screen.getByText('A long-term compass that guides related community decisions.')).toBeInTheDocument();

    // Check that conversation section is rendered
    expect(screen.getByText('Community reasoning')).toBeInTheDocument();

    // Check that background section is rendered
    expect(screen.getByText('Background')).toBeInTheDocument();

    // Check that share button is rendered
    expect(screen.getByText('Share')).toBeInTheDocument();
  });

  it('redirects non-level_a polls to proposals page', async () => {
    // Mock API responses
    vi.mocked(getPoll).mockResolvedValue({
      id: 'test-id',
      title: 'Test Proposal',
      description: 'Test description',
      decision_type: 'level_b' as const,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      created_by: 'user-1',
      is_active: true,
      labels: []
    });

    vi.mocked(getMyVoteForPoll).mockResolvedValue(null);
    vi.mocked(getResults).mockResolvedValue({ poll_id: 'test-id', total_votes: 0, options: [] });

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for redirect
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/proposals/test-id', { replace: true });
    });
  });

  it('shows loading state initially', () => {
    vi.mocked(getPoll).mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Check that loading skeleton is shown
    expect(screen.queryByText('Test Compass')).not.toBeInTheDocument();
    expect(screen.queryByText('Compass unavailable')).not.toBeInTheDocument();
    
    // Check for loading skeleton elements with animate-pulse class
    const skeletonElements = document.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('shows error state when API fails', async () => {
    vi.mocked(getPoll).mockRejectedValue(new Error('API Error'));
    vi.mocked(getPollOptions).mockRejectedValue(new Error('API Error'));
    vi.mocked(getMyVoteForPoll).mockRejectedValue(new Error('API Error'));
    vi.mocked(getResults).mockRejectedValue(new Error('API Error'));

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText('Compass unavailable')).toBeInTheDocument();
      expect(screen.getByText('API Error')).toBeInTheDocument();
      expect(screen.getByText('Try again')).toBeInTheDocument();
    });
  });
});
