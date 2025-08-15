import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import PrincipleDocPage from '../PrincipleDocPage';
import { getPoll, listComments, createComment } from '../../lib/api';

// Mock the API functions
vi.mock('../../lib/api', () => ({
  getPoll: vi.fn(),
  listComments: vi.fn(),
  createComment: vi.fn(),
}));

// Mock the Toaster
vi.mock('../../components/ui/useToast', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

const mockPoll = {
  id: 'test-poll-1',
  title: 'Test Principle',
  description: 'Test description',
  longform_main: 'This is the main community document content.',
  extra: {
    counter_body: 'This is the counter document content.',
    evidence: [
      {
        title: 'Test Source',
        source: 'Test Organization',
        year: 2023,
        url: 'https://example.com'
      }
    ]
  },
  created_at: '2025-01-10T10:00:00Z',
  updated_at: '2025-01-10T10:00:00Z',
  decision_type: 'level_a' as const,
  created_by: 'test-user',
  is_active: true,
  labels: []
};

const mockComments = {
  comments: [
    {
      id: 'comment-1',
      poll_id: 'test-poll-1',
      user: { id: 'user-1', username: 'testuser' },
      body: 'This is a revision proposal',
      created_at: '2025-01-10T10:00:00Z',
      up_count: 0,
      down_count: 0,
      kind: 'revision',
      stance: 'main' as const
    }
  ],
  total: 1,
  limit: 20,
  offset: 0,
  has_more: false
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('PrincipleDocPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: { pathname: '/compass/test-poll-1' },
      writable: true
    });
  });

  it('renders community and counter documents with collapsible content', async () => {
    vi.mocked(getPoll).mockResolvedValue(mockPoll);
    vi.mocked(listComments).mockResolvedValue(mockComments);

    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Principle')).toBeInTheDocument();
    });

    expect(screen.getByText('Community document')).toBeInTheDocument();
    expect(screen.getByText('Counter-document')).toBeInTheDocument();
    expect(screen.getByText('This is the main community document content.')).toBeInTheDocument();
    expect(screen.getByText('This is the counter document content.')).toBeInTheDocument();
  });

  it('enforces 240-1000 character limit in composer', async () => {
    vi.mocked(getPoll).mockResolvedValue(mockPoll);
    vi.mocked(listComments).mockResolvedValue(mockComments);

    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByText('Share a revision or counterpoint')).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/Propose a change/);
    const submitButton = screen.getByText('Post revision');

    // Initially disabled (too short)
    expect(submitButton).toBeDisabled();

    // Add valid content
    fireEvent.change(textarea, {
      target: { value: 'a'.repeat(240) }
    });
    expect(submitButton).not.toBeDisabled();

    // Add too much content
    fireEvent.change(textarea, {
      target: { value: 'a'.repeat(1001) }
    });
    expect(submitButton).toBeDisabled();
  });

  it('posts revision and optimistically adds to list', async () => {
    vi.mocked(getPoll).mockResolvedValue(mockPoll);
    vi.mocked(listComments).mockResolvedValue(mockComments);
    vi.mocked(createComment).mockResolvedValue({
      id: 'new-comment',
      poll_id: 'test-poll-1',
      user: { id: 'user-1', username: 'testuser' },
      body: 'New revision proposal',
      created_at: '2025-01-10T11:00:00Z',
      up_count: 0,
      down_count: 0,
      kind: 'revision',
      stance: 'main' as const
    });

    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByText('Share a revision or counterpoint')).toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText(/Propose a change/);
    const submitButton = screen.getByText('Post revision');

    fireEvent.change(textarea, {
      target: { value: 'a'.repeat(240) }
    });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(createComment).toHaveBeenCalledWith('test-poll-1', {
        body: 'a'.repeat(240),
        kind: 'revision',
        stance: 'main'
      });
    });
  });

  it('shows evidence panel with external links', async () => {
    vi.mocked(getPoll).mockResolvedValue(mockPoll);
    vi.mocked(listComments).mockResolvedValue(mockComments);

    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByText('About this')).toBeInTheDocument();
    });

    expect(screen.getByText('Test Source')).toBeInTheDocument();
    expect(screen.getByText('Test Organization, 2023')).toBeInTheDocument();

    const link = screen.getByRole('link', { name: /Test Source/ });
    expect(link).toHaveAttribute('href', 'https://example.com');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('handles error states with retry buttons', async () => {
    vi.mocked(getPoll).mockRejectedValue(new Error('Failed to load'));
    vi.mocked(listComments).mockResolvedValue(mockComments);

    renderWithRouter(<PrincipleDocPage />);

    await waitFor(() => {
      expect(screen.getByText('Error loading content')).toBeInTheDocument();
    });

    expect(screen.getByText('Retry')).toBeInTheDocument();
  });
});
