import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import CompassPage, { type RetryScheduler } from '../CompassPage';
import { getPoll, getPollOptions, getMyVoteForPoll, castVote, getResults, listComments } from '../../lib/api';
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
  castVote: vi.fn(),
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
    directionsTitle: "Choose a direction to align with",
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

describe('CompassPage Voting', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('allows user to select and submit alignment', async () => {
    const mockPoll = {
      id: 'test-id',
      title: 'Test Compass',
      description: 'Test description',
      decision_type: 'level_a' as const,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      labels: []
    };

    const mockOptions = [
      { id: 'option-1', poll_id: 'test-id', text: 'Direction A', created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
      { id: 'option-2', poll_id: 'test-id', text: 'Direction B', created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' }
    ];

    const mockResults = {
      poll_id: 'test-id',
      total_votes: 1,
      options: [
        { option_id: 'option-1', votes: 1 },
        { option_id: 'option-2', votes: 0 }
      ]
    };

    (getPoll as any).mockResolvedValue(mockPoll);
    (getPollOptions as any).mockResolvedValue(mockOptions);
    (getMyVoteForPoll as any).mockResolvedValue(null);
    (castVote as any).mockResolvedValue({ success: true });
    (getResults as any).mockResolvedValue(mockResults);
    (listComments as any).mockResolvedValue({ comments: [], total: 0, limit: 10, offset: 0, has_more: false });

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Compass')).toBeInTheDocument();
    });

    // Check that direction cards are rendered
    expect(screen.getByTestId('direction-title-option-1')).toBeInTheDocument();
    expect(screen.getByTestId('direction-title-option-2')).toBeInTheDocument();

    // Click on first direction card
    const firstCard = screen.getByTestId('direction-card-option-1');
    fireEvent.click(firstCard);

    // Click the align button
    const alignButton = screen.getByTestId('align-btn-option-1');
    fireEvent.click(alignButton);

    // Verify API call was made
    await waitFor(() => {
      expect(castVote).toHaveBeenCalledWith('test-id', 'option-1');
    });

    // Verify confirmation banner appears
    await waitFor(() => {
      expect(screen.getByTestId('alignment-banner')).toBeInTheDocument();
      expect(screen.getByText(/You're aligned with/)).toBeInTheDocument();
      expect(screen.getByTestId('direction-title-option-1')).toHaveTextContent('Direction A');
    });

    // Verify direction cards are disabled
    const firstCardAfterVote = screen.getByTestId('direction-card-option-1');
    expect(firstCardAfterVote).toHaveClass('opacity-75');
    expect(firstCardAfterVote).toHaveAttribute('tabindex', '-1');
  });

  it('shows existing alignment on load', async () => {
    const mockPoll = {
      id: 'test-id',
      title: 'Test Compass',
      description: 'Test description',
      decision_type: 'level_a' as const,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      labels: []
    };

    const mockOptions = [
      { id: 'option-1', poll_id: 'test-id', text: 'Direction A', created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
      { id: 'option-2', poll_id: 'test-id', text: 'Direction B', created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' }
    ];

    const mockMyVote = {
      poll_id: 'test-id',
      option_id: 'option-1',
      created_at: '2023-01-01T10:00:00Z'
    };

    const mockResults = {
      poll_id: 'test-id',
      total_votes: 1,
      options: [
        { option_id: 'option-1', votes: 1 },
        { option_id: 'option-2', votes: 0 }
      ]
    };

    (getPoll as any).mockResolvedValue(mockPoll);
    (getPollOptions as any).mockResolvedValue(mockOptions);
    (getMyVoteForPoll as any).mockResolvedValue(mockMyVote);
    (getResults as any).mockResolvedValue(mockResults);
    (listComments as any).mockResolvedValue({ comments: [], total: 0, limit: 10, offset: 0, has_more: false });

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Compass')).toBeInTheDocument();
    });

    // Verify confirmation banner appears immediately
    await waitFor(() => {
      expect(screen.getByTestId('alignment-banner')).toBeInTheDocument();
      expect(screen.getByText(/You're aligned with/)).toBeInTheDocument();
      expect(screen.getByTestId('direction-title-option-1')).toHaveTextContent('Direction A');
    });

    // Verify direction cards are disabled
    const firstCard = screen.getByTestId('direction-card-option-1');
    expect(firstCard).toHaveClass('opacity-75');
    expect(firstCard).toHaveAttribute('tabindex', '-1');
  });

  it('allows changing alignment', async () => {
    const mockPoll = {
      id: 'test-id',
      title: 'Test Compass',
      description: 'Test description',
      decision_type: 'level_a' as const,
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      labels: []
    };

    const mockOptions = [
      { id: 'option-1', poll_id: 'test-id', text: 'Direction A', created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' },
      { id: 'option-2', poll_id: 'test-id', text: 'Direction B', created_at: '2023-01-01T00:00:00Z', updated_at: '2023-01-01T00:00:00Z' }
    ];

    const mockMyVote = {
      poll_id: 'test-id',
      option_id: 'option-1',
      created_at: '2023-01-01T10:00:00Z'
    };

    const mockResults = {
      poll_id: 'test-id',
      total_votes: 1,
      options: [
        { option_id: 'option-1', votes: 1 },
        { option_id: 'option-2', votes: 0 }
      ]
    };

    (getPoll as any).mockResolvedValue(mockPoll);
    (getPollOptions as any).mockResolvedValue(mockOptions);
    (getMyVoteForPoll as any).mockResolvedValue(mockMyVote);
    (getResults as any).mockResolvedValue(mockResults);
    (listComments as any).mockResolvedValue({ comments: [], total: 0, limit: 10, offset: 0, has_more: false });

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Compass')).toBeInTheDocument();
    });

    // Verify confirmation banner is shown
    await waitFor(() => {
      expect(screen.getByTestId('alignment-banner')).toBeInTheDocument();
    });

    // Click "Change alignment" button
    const changeButton = screen.getByText('Change alignment');
    fireEvent.click(changeButton);

    // Verify confirmation banner is hidden
    await waitFor(() => {
      expect(screen.queryByTestId('alignment-banner')).not.toBeInTheDocument();
    });

    // Verify direction cards are enabled again
    const firstCard = screen.getByTestId('direction-card-option-1');
    expect(firstCard).not.toHaveClass('opacity-75');
    expect(firstCard).toHaveAttribute('tabindex', '0');
  });
});
