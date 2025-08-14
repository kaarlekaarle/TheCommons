import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import CompassPage, { type RetryScheduler } from '../CompassPage';
import { getPoll, getPollOptions, getMyVoteForPoll, getResults, listComments, createComment } from '../../lib/api';
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
  createComment: vi.fn(),
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

describe('CompassPage Conversation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads and displays existing comments', async () => {
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

    const mockComments = {
      comments: [
        {
          id: 'comment-1',
          poll_id: 'test-id',
          user: { id: 'user-1', username: 'Alice' },
          body: 'This direction aligns with my values and vision for the future.',
          created_at: '2023-01-01T10:00:00Z',
          up_count: 2,
          down_count: 0,
          my_reaction: null
        },
        {
          id: 'comment-2',
          poll_id: 'test-id',
          user: { id: 'user-2', username: 'Bob' },
          body: 'I think this approach will lead to better outcomes for everyone.',
          created_at: '2023-01-01T11:00:00Z',
          up_count: 1,
          down_count: 0,
          my_reaction: null
        }
      ],
      total: 2,
      limit: 10,
      offset: 0,
      has_more: false
    };

    (getPoll as any).mockResolvedValue(mockPoll);
    (getPollOptions as any).mockResolvedValue(mockOptions);
    (getMyVoteForPoll as any).mockResolvedValue(null);
    (getResults as any).mockResolvedValue({
      poll_id: 'test-id',
      total_votes: 0,
      options: []
    });
    (listComments as any).mockResolvedValue(mockComments);

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Compass')).toBeInTheDocument();
    });

    // Verify comments are loaded
    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('Bob')).toBeInTheDocument();
      expect(screen.getByText('This direction aligns with my values and vision for the future.')).toBeInTheDocument();
      expect(screen.getByText('I think this approach will lead to better outcomes for everyone.')).toBeInTheDocument();
    });
  });

  it('allows posting new reasoning', async () => {
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

    const mockComments = {
      comments: [],
      total: 0,
      limit: 10,
      offset: 0,
      has_more: false
    };

    const newComment = {
      id: 'comment-new',
      poll_id: 'test-id',
      user: { id: 'user-me', username: 'You' },
      body: 'This is my reasoning for choosing this direction. It aligns with my values and I believe it will lead to positive outcomes for our community.',
      created_at: '2023-01-01T12:00:00Z',
      up_count: 0,
      down_count: 0,
      my_reaction: null
    };

    (getPoll as any).mockResolvedValue(mockPoll);
    (getPollOptions as any).mockResolvedValue(mockOptions);
    (getMyVoteForPoll as any).mockResolvedValue(null);
    (getResults as any).mockResolvedValue({
      poll_id: 'test-id',
      total_votes: 0,
      options: []
    });
    (listComments as any).mockResolvedValue(mockComments);
    (createComment as any).mockResolvedValue(newComment);

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Compass')).toBeInTheDocument();
    });

    // Debug: Check if conversation section is rendered
    await waitFor(() => {
      expect(screen.getByText('Community reasoning')).toBeInTheDocument();
    });

    // Verify character counter is visible immediately
    expect(screen.getByTestId('char-counter')).toBeInTheDocument();
    expect(screen.getByTestId('char-counter')).toHaveTextContent('0/1000');

    // Find the textarea and type reasoning
    const textarea = screen.getByLabelText('Share why you lean this way');
    const reasoning = 'This is my reasoning for choosing this direction. It aligns with my values and I believe it will lead to positive outcomes for our community. I think this approach will benefit everyone in the long run. This direction represents a fundamental shift in how we approach decision-making, focusing on long-term sustainability and community well-being rather than short-term gains. I believe this will create a more resilient and equitable future for all members of our community.';
    
    fireEvent.change(textarea, { target: { value: reasoning } });

    // Verify character count updates to the actual length
    const expectedLength = reasoning.length;
    await waitFor(() => {
      expect(screen.getByTestId('char-counter')).toHaveTextContent(`${expectedLength}/1000`);
    });

    // Check if submit button is enabled after typing
    const submitButton = screen.getByTestId('submit-reasoning') as HTMLButtonElement;
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });

    // Submit the form
    fireEvent.click(submitButton);

    // Verify API call was made
    await waitFor(() => {
      expect(createComment).toHaveBeenCalledWith('test-id', { body: reasoning });
    });

    // Verify new comment appears in list
    await waitFor(() => {
      expect(screen.getByText('You')).toBeInTheDocument();
      expect(screen.getByText('This is my reasoning for choosing this direction. It aligns with my values and I believe it will lead to positive outcomes for our community.')).toBeInTheDocument();
    });
  });

  it('prevents posting reasoning under minimum length', async () => {
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

    const mockComments = {
      comments: [],
      total: 0,
      limit: 10,
      offset: 0,
      has_more: false
    };

    (getPoll as any).mockResolvedValue(mockPoll);
    (getPollOptions as any).mockResolvedValue(mockOptions);
    (getMyVoteForPoll as any).mockResolvedValue(null);
    (getResults as any).mockResolvedValue({
      poll_id: 'test-id',
      total_votes: 0,
      options: []
    });
    (listComments as any).mockResolvedValue(mockComments);

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Compass')).toBeInTheDocument();
    });

    // Verify character counter is visible
    expect(screen.getByTestId('char-counter')).toBeInTheDocument();

    // Find the textarea and type short reasoning
    const textarea = screen.getByLabelText('Share why you lean this way');
    const shortReasoning = 'This is too short.';
    
    fireEvent.change(textarea, { target: { value: shortReasoning } });

    // Verify character count updates
    await waitFor(() => {
      expect(screen.getByTestId('char-counter')).toHaveTextContent('18/1000');
    });

    // Submit button should be disabled
    const submitButton = screen.getByTestId('submit-reasoning');
    expect(submitButton).toBeDisabled();

    // Try to submit
    fireEvent.click(submitButton);

    // Verify API call was NOT made
    await waitFor(() => {
      expect(createComment).not.toHaveBeenCalled();
    });
  });

  it('shows empty state when no comments exist', async () => {
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

    const mockComments = {
      comments: [],
      total: 0,
      limit: 10,
      offset: 0,
      has_more: false
    };

    (getPoll as any).mockResolvedValue(mockPoll);
    (getPollOptions as any).mockResolvedValue(mockOptions);
    (getMyVoteForPoll as any).mockResolvedValue(null);
    (getResults as any).mockResolvedValue({
      poll_id: 'test-id',
      total_votes: 0,
      options: []
    });
    (listComments as any).mockResolvedValue(mockComments);

    renderWithRouter(<CompassPage scheduler={immediateScheduler} />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByText('Test Compass')).toBeInTheDocument();
    });

    // Verify empty state is shown
    await waitFor(() => {
      expect(screen.getByText('Be the first to share your reasoning.')).toBeInTheDocument();
    });
  });
});
