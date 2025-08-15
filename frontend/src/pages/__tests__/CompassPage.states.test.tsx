import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import CompassPage, { type RetryScheduler, computeBackoff } from '../CompassPage';
import * as api from '../../lib/api';
import * as analytics from '../../lib/analytics';
import { ToasterProvider } from '../../components/ui/Toaster';
import type { Poll } from '../../types';

// Mock the API
vi.mock('../../lib/api');
vi.mock('../../lib/analytics');
vi.mock('../../config/flags', () => ({
  flags: {
    compassEnabled: true
  }
}));

// Test scheduler that resolves immediately
const immediateScheduler: RetryScheduler = {
  wait: () => Promise.resolve()
};

// Helper to flush all microtasks
const flushAll = () => new Promise(res => setTimeout(res, 0));

// Helper to render with route
const renderWithRoute = (component: React.ReactElement, options: { route: string }) => {
  return render(
    <ToasterProvider>
      <MemoryRouter initialEntries={[options.route]}>
        <Routes>
          <Route path="/compass/:id" element={component} />
        </Routes>
      </MemoryRouter>
    </ToasterProvider>
  );
};

// Deferred promise helper for cancellation tests
const defer = <T,>() => {
  let resolve!: (v: T) => void, reject!: (e?: any) => void;
  const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
};

// Mock data
const mockPoll: Poll = {
  id: 'test-poll-id',
  title: 'Level A Principle (Placeholder)',
  description: 'This is a placeholder example for Level A.',
  created_by: 'test-user',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  is_active: true,
  end_date: '2025-12-31T00:00:00Z',
  decision_type: 'level_a',
  direction_choice: 'Placeholder'
};

const mockOptions = [
  { id: 'option-1', poll_id: 'test-poll-1', text: 'Direction A', created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' },
  { id: 'option-2', poll_id: 'test-poll-1', text: 'Direction B', created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' }
];

const mockResults = {
  poll_id: 'test-poll-1',
  total_votes: 8,
  options: [
    { option_id: 'option-1', text: 'Direction A', votes: 5, percentage: 62.5 },
    { option_id: 'option-2', text: 'Direction B', votes: 3, percentage: 37.5 }
  ]
};

const mockComments = {
  comments: [
    {
      id: 'comment-1',
      poll_id: 'test-poll-1',
      body: 'This is a test comment',
      created_at: '2024-01-01T00:00:00Z',
      user: { id: 'user-1', username: 'testuser', name: 'Test User' },
      up_count: 0,
      down_count: 0
    }
  ],
  total: 1,
  limit: 10,
  offset: 0,
  has_more: false
};

describe('CompassPage States', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock computeBackoff to return 0 for immediate retries
    vi.spyOn({ computeBackoff }, 'computeBackoff').mockReturnValue(0);

    // Default successful mocks
    vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
    vi.mocked(api.getPollOptions).mockResolvedValue(mockOptions);
    vi.mocked(api.getMyVoteForPoll).mockResolvedValue(null);
    vi.mocked(api.getResults).mockResolvedValue(mockResults);
    vi.mocked(api.listComments).mockResolvedValue(mockComments);
    vi.mocked(api.createComment).mockResolvedValue(mockComments.comments[0]);
    vi.mocked(api.castVote).mockResolvedValue({
      id: 'vote-1',
      poll_id: 'test-poll-1',
      option_id: 'option-1',
      voter_id: 'user-1',
      created_at: '2024-01-01T00:00:00Z'
    });

    // Mock analytics
    vi.mocked(analytics.compassAnalytics).view = vi.fn();
    vi.mocked(analytics.compassAnalytics).alignSubmit = vi.fn();
    vi.mocked(analytics.compassAnalytics).alignSuccess = vi.fn();
    vi.mocked(analytics.compassAnalytics).reasonSubmit = vi.fn();
    vi.mocked(analytics.compassAnalytics).reasonSuccess = vi.fn();
    vi.mocked(analytics.compassAnalytics).refetch = vi.fn();
    vi.mocked(analytics.compassAnalytics).error = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Loading States', () => {
    it('shows loading skeleton initially', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      expect(screen.getByTestId('compass-skeleton')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });
    });

    it('shows no layout shift during loading', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      const skeleton = screen.getByTestId('compass-skeleton');
      expect(skeleton).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      expect(skeleton).not.toBeInTheDocument();
    });
  });

  describe('Empty States', () => {
    it('shows empty state when no directions available', async () => {
      vi.mocked(api.getPollOptions).mockResolvedValue([]);

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Direction A')).toBeInTheDocument();
        expect(screen.getByText('Direction B')).toBeInTheDocument();
      });
    });

    it('shows empty state when no alignments yet', async () => {
      vi.mocked(api.getResults).mockResolvedValue({
        poll_id: 'test-poll-1',
        total_votes: 0,
        options: []
      });

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Community alignment (so far)')).toBeInTheDocument();
        expect(screen.getByText('No alignments yet')).toBeInTheDocument();
      });
    });

    it('shows empty state when no conversation yet', async () => {
      vi.mocked(api.listComments).mockResolvedValue({
        comments: [],
        total: 0,
        limit: 10,
        offset: 0,
        has_more: false
      });

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Take part in the conversation')).toBeInTheDocument();
        expect(screen.getByText('No conversation yet')).toBeInTheDocument();
      });
    });
  });

  describe('Error States', () => {
    it('shows error state when directions fail to load', async () => {
      vi.mocked(api.getPoll).mockRejectedValue({ message: 'Network error' });

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Try again')).toBeInTheDocument();
      });
    });

    it('shows error state when tally fails but directions load', async () => {
      vi.mocked(api.getResults).mockRejectedValue({ message: 'Results unavailable' });

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Could not load alignment results')).toBeInTheDocument();
      });
    });

    it('shows error state when conversation fails', async () => {
      vi.mocked(api.listComments).mockRejectedValue({ message: 'Comments unavailable' });

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });
    });
  });

  describe('Retry Functionality', () => {
    it('retries directions section on error', async () => {
      // Mock first call to fail, second to succeed
      vi.mocked(api.getPoll)
        .mockRejectedValueOnce({ message: 'Network error' })
        .mockResolvedValueOnce(mockPoll);

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Try again')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Try again'));

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      expect(analytics.compassAnalytics.refetch).toHaveBeenCalledWith('directions', 1);
    });

    it('retries tally section on error', async () => {
      vi.mocked(api.getResults)
        .mockRejectedValueOnce({ message: 'Results unavailable' })
        .mockResolvedValueOnce(mockResults);

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Could not load alignment results')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Try again'));

      await waitFor(() => {
        expect(screen.getByText('Community alignment (so far)')).toBeInTheDocument();
      });

      expect(analytics.compassAnalytics.refetch).toHaveBeenCalledWith('tally', 1);
    });

    it('limits retry attempts to 3', async () => {
      vi.mocked(api.getPoll).mockRejectedValue({ message: 'Network error' });

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Try again')).toBeInTheDocument();
      });

      // Click retry 4 times (only first 3 should work)
      for (let i = 0; i < 4; i++) {
        fireEvent.click(screen.getByText('Try again'));
        if (i < 3) {
          await waitFor(() => {
            expect(analytics.compassAnalytics.refetch).toHaveBeenCalledWith('directions', i + 1);
          });
        }
      }

      // Should not call retry more than 3 times
      expect(analytics.compassAnalytics.refetch).toHaveBeenCalledTimes(3);
    });
  });

  describe('Request Cancellation', () => {
    it('cancels requests on route change', async () => {
      // Create deferred promises we can control
      const first = defer<any>();
      const second = defer<any>();

      // Mock getPoll to return our controlled promises
      vi.mocked(api.getPoll)
        .mockReturnValueOnce(first.promise)
        .mockReturnValueOnce(second.promise);

      const { rerender } = renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      // Wait for first request to be made
      await waitFor(() => {
        expect(api.getPoll).toHaveBeenCalledWith('test-poll-1', expect.any(AbortSignal));
      });

      // Navigate to different route
      rerender(
        <ToasterProvider>
          <MemoryRouter initialEntries={['/compass/different-poll-id']}>
            <Routes>
              <Route path="/compass/:id" element={<CompassPage scheduler={immediateScheduler} />} />
            </Routes>
          </MemoryRouter>
        </ToasterProvider>
      );

      // Resolve the second promise
      second.resolve(mockPoll);

      // Should make a new request for the different poll ID
      await waitFor(() => {
        expect(api.getPoll).toHaveBeenCalledTimes(2);
        expect(api.getPoll).toHaveBeenCalledWith('different-poll-id', expect.any(AbortSignal));
      });
    });
  });

  describe('Accessibility', () => {
    it('has correct heading hierarchy', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      // Check for single H1
      const h1Elements = screen.getAllByRole('heading', { level: 1 });
      expect(h1Elements).toHaveLength(1);
      expect(h1Elements[0]).toHaveTextContent('Level A Principle (Placeholder)');

      // Check for H2 section headings
      const h2Elements = screen.getAllByRole('heading', { level: 2 });
      expect(h2Elements.length).toBeGreaterThan(0);

      const h2Texts = h2Elements.map(el => el.textContent);
      expect(h2Texts).toContain('Choose a direction to align with');
      expect(h2Texts).toContain('Community alignment (so far)');
      expect(h2Texts).toContain('Take part in the conversation');
      expect(h2Texts).toContain('Background');
    });

    it('has properly labelled form inputs', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      // Check for labelled textarea
      const textarea = screen.getByLabelText('Share why you lean this way');
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveAttribute('aria-describedby', 'char-counter reasoning-helper');

      // Check for helper text
      expect(screen.getByText('Short essay. 240–1000 characters.')).toBeInTheDocument();

      // Check for character counter
      expect(screen.getByTestId('char-counter')).toBeInTheDocument();
    });

    it('has visible focus indicators', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      // Check that buttons have focus indicators
      const buttons = screen.getAllByRole('button').filter(button =>
        button.tagName === 'BUTTON' && !button.classList.contains('rounded-full')
      );

      buttons.forEach(button => {
        expect(button).toHaveClass('focus-ring');
      });
    });

    it('has live regions for status updates', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      // Check for aria-live regions
      const liveRegions = screen.getAllByRole('status');
      expect(liveRegions.length).toBeGreaterThan(0);
    });
  });

  describe('Analytics', () => {
    it('tracks page view on load', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      expect(analytics.compassAnalytics.view).toHaveBeenCalledWith('test-poll-1');
    });

    it('tracks alignment submission and success', async () => {
      vi.mocked(api.castVote).mockResolvedValue({
        id: 'vote-1',
        poll_id: 'test-poll-1',
        option_id: 'option-1',
        voter_id: 'user-1',
        created_at: '2024-01-01T00:00:00Z'
      });

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Align with this direction'));

      await waitFor(() => {
        expect(analytics.compassAnalytics.alignSubmit).toHaveBeenCalledWith('test-poll-1', 'option-1');
        expect(analytics.compassAnalytics.alignSuccess).toHaveBeenCalledWith('test-poll-1', 'option-1');
      });
    });

    it('tracks reasoning submission and success', async () => {
      const mockComment = {
        id: 'comment-1',
        poll_id: 'test-poll-1',
        body: 'This is a test comment that meets the minimum character requirement for submission. It needs to be at least 240 characters long to be considered valid. This should be enough to meet that requirement and allow the test to pass successfully.',
        created_at: '2024-01-01T00:00:00Z',
        user: { id: 'user-1', username: 'testuser', name: 'Test User' },
        up_count: 0,
        down_count: 0
      };

      vi.mocked(api.createComment).mockResolvedValue(mockComment);

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      const textarea = screen.getByLabelText('Share why you lean this way');
      fireEvent.change(textarea, {
        target: { value: 'This is a test comment that meets the minimum character requirement for submission. It needs to be at least 240 characters long to be considered valid. This should be enough to meet that requirement and allow the test to pass successfully.' }
      });

      const submitButton = screen.getByText('Share reasoning');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(analytics.compassAnalytics.reasonSubmit).toHaveBeenCalled();
        expect(analytics.compassAnalytics.reasonSuccess).toHaveBeenCalled();
      });
    });

    it('tracks errors', async () => {
      vi.mocked(api.getPoll).mockRejectedValue({ message: 'Network error' });

      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Try again')).toBeInTheDocument();
      });

      expect(analytics.compassAnalytics.error).toHaveBeenCalledWith('directions', 'Network error');
    });
  });

  describe('Character Counter', () => {
    it('shows character count immediately', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      expect(screen.getByTestId('char-counter')).toHaveTextContent('0/1000');
    });

    it('updates character count as user types', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      const textarea = screen.getByLabelText('Share why you lean this way');
      fireEvent.change(textarea, { target: { value: 'Hello world' } });

      expect(screen.getByTestId('char-counter')).toHaveTextContent('11/1000');
    });

    it('enforces character limits', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      const textarea = screen.getByLabelText('Share why you lean this way');
      const validText = 'This is a test comment that meets the minimum character requirement for submission. It needs to be at least 240 characters long to be considered valid. This should be enough to meet that requirement and allow the test to pass successfully.';

      fireEvent.change(textarea, { target: { value: validText } });

      const submitButton = screen.getByText('Share reasoning');
      expect(submitButton).not.toBeDisabled();

      // Test minimum length
      fireEvent.change(textarea, { target: { value: 'Too short' } });
      expect(submitButton).toBeDisabled();

      // Test maximum length
      const longText = 'a'.repeat(1001);
      fireEvent.change(textarea, { target: { value: longText } });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('New Layout and Content', () => {
    it('shows the question section', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      expect(screen.getByText('The Question')).toBeInTheDocument();
      expect(screen.getByText(/This is a placeholder example for Level A/)).toBeInTheDocument();
    });

    it('shows read more buttons in direction cards', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      const readMoreButtons = screen.getAllByText('Read more');
      expect(readMoreButtons.length).toBeGreaterThan(0);
    });

    it('expands direction details when read more is clicked', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      const readMoreButtons = screen.getAllByText('Read more');
      fireEvent.click(readMoreButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Why choose this direction?')).toBeInTheDocument();
        expect(screen.getByText('This is a placeholder rationale point.')).toBeInTheDocument();
      });
    });

    it('shows background section with read more', async () => {
      renderWithRoute(<CompassPage scheduler={immediateScheduler} />, { route: '/compass/test-poll-1' });

      await waitFor(() => {
        expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
      });

      expect(screen.getByText('Background')).toBeInTheDocument();
      expect(screen.getByText(/This is a placeholder background summary/)).toBeInTheDocument();

      const backgroundReadMore = screen.getAllByText('Read more').find(button =>
        button.closest('section')?.textContent?.includes('Background')
      );
      expect(backgroundReadMore).toBeInTheDocument();
    });
  });
});
