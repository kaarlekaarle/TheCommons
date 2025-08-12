import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DelegationStatus from '../DelegationStatus';
import * as api from '../../../lib/api';

// Mock the API functions
vi.mock('../../../lib/api', () => ({
  getMyDelegation: vi.fn(),
}));

// Mock analytics
vi.mock('../../../lib/analytics', () => ({
  trackDelegationViewed: vi.fn(),
  trackDelegationOpened: vi.fn(),
}));

describe('DelegationStatus', () => {
  const mockOnOpenModal = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Compact Mode', () => {
    it('should render compact status when no delegation exists', async () => {
      vi.mocked(api.getMyDelegation).mockResolvedValue({});

      render(
        <DelegationStatus
          compact={true}
          onOpenModal={mockOnOpenModal}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('No delegation')).toBeInTheDocument();
      });
    });

    it('should render compact status with global delegation', async () => {
      const mockDelegation = {
        global: {
          to_user_id: 'user-123',
          to_user_name: 'Alice',
          active: true,
          chain: []
        }
      };

      vi.mocked(api.getMyDelegation).mockResolvedValue(mockDelegation);

      render(
        <DelegationStatus
          compact={true}
          onOpenModal={mockOnOpenModal}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Delegating to Alice')).toBeInTheDocument();
      });
    });

    it('should render compact status with chain information', async () => {
      const mockDelegation = {
        global: {
          to_user_id: 'user-123',
          to_user_name: 'Alice',
          active: true,
          chain: [
            { user_id: 'user-456', user_name: 'Bob' },
            { user_id: 'user-789', user_name: 'Charlie' }
          ]
        }
      };

      vi.mocked(api.getMyDelegation).mockResolvedValue(mockDelegation);

      render(
        <DelegationStatus
          compact={true}
          onOpenModal={mockOnOpenModal}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Delegating to Alice • 2-hop chain')).toBeInTheDocument();
      });
    });

    it('should call onOpenModal when clicked', async () => {
      vi.mocked(api.getMyDelegation).mockResolvedValue({});

      render(
        <DelegationStatus
          compact={true}
          onOpenModal={mockOnOpenModal}
        />
      );

      await waitFor(() => {
        const statusElement = screen.getByRole('button');
        fireEvent.click(statusElement);
        expect(mockOnOpenModal).toHaveBeenCalled();
      });
    });

    it('should handle keyboard navigation', async () => {
      vi.mocked(api.getMyDelegation).mockResolvedValue({});

      render(
        <DelegationStatus
          compact={true}
          onOpenModal={mockOnOpenModal}
        />
      );

      await waitFor(() => {
        const statusElement = screen.getByRole('button');
        
        // Test Enter key
        fireEvent.keyDown(statusElement, { key: 'Enter' });
        expect(mockOnOpenModal).toHaveBeenCalled();
        
        // Reset mock
        mockOnOpenModal.mockClear();
        
        // Test Space key
        fireEvent.keyDown(statusElement, { key: ' ' });
        expect(mockOnOpenModal).toHaveBeenCalled();
      });
    });

    it('should have proper accessibility attributes', async () => {
      vi.mocked(api.getMyDelegation).mockResolvedValue({});

      render(
        <DelegationStatus
          compact={true}
          onOpenModal={mockOnOpenModal}
        />
      );

      await waitFor(() => {
        const statusElement = screen.getByRole('button');
        expect(statusElement).toHaveAttribute('aria-label', 'Manage delegation');
        expect(statusElement).toHaveAttribute('tabIndex', '0');
      });
    });
  });

  describe('Full Mode', () => {
    it('should render full status when no delegation exists', async () => {
      vi.mocked(api.getMyDelegation).mockResolvedValue({});

      render(<DelegationStatus />);

      await waitFor(() => {
        expect(screen.getByText('You currently vote for yourself.')).toBeInTheDocument();
        expect(screen.getByText('Manage…')).toBeInTheDocument();
      });
    });

    it('should render full status with global delegation', async () => {
      const mockDelegation = {
        global: {
          to_user_id: 'user-123',
          to_user_name: 'Alice',
          active: true,
          chain: []
        }
      };

      vi.mocked(api.getMyDelegation).mockResolvedValue(mockDelegation);

      render(<DelegationStatus />);

      await waitFor(() => {
        expect(screen.getByText('You delegate globally to Alice.')).toBeInTheDocument();
        expect(screen.getByText('Manage…')).toBeInTheDocument();
      });
    });

    it('should render full status with poll-specific delegation', async () => {
      const mockDelegation = {
        poll: {
          poll_id: 'poll-123',
          to_user_id: 'user-123',
          to_user_name: 'Alice',
          active: true,
          chain: []
        }
      };

      vi.mocked(api.getMyDelegation).mockResolvedValue(mockDelegation);

      render(<DelegationStatus pollId="poll-123" />);

      await waitFor(() => {
        expect(screen.getByText('You delegate this poll to Alice.')).toBeInTheDocument();
        expect(screen.getByText('Manage…')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should show error message when API fails', async () => {
      vi.mocked(api.getMyDelegation).mockRejectedValue({
        message: 'Failed to load delegation'
      });

      render(<DelegationStatus />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load delegation')).toBeInTheDocument();
      });
    });

    it('should show loading state', async () => {
      // Don't resolve the promise immediately
      vi.mocked(api.getMyDelegation).mockImplementation(() => new Promise(() => {}));

      render(<DelegationStatus />);

      expect(screen.getByText('Checking delegation…')).toBeInTheDocument();
    });
  });
});
