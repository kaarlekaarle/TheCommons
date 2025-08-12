import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ManageDelegationModal from '../ManageDelegationModal';
import * as api from '../../../lib/api';

// Mock the API functions
vi.mock('../../../lib/api', () => ({
  searchUsers: vi.fn(),
  createDelegation: vi.fn(),
  removeDelegation: vi.fn(),
  getMyDelegation: vi.fn(),
}));

describe('ManageDelegationModal', () => {
  const mockOnClose = vi.fn();
  const mockOnDelegationChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render create mode when no delegation exists', async () => {
    vi.mocked(api.getMyDelegation).mockResolvedValue({});

    render(
      <ManageDelegationModal
        open={true}
        onClose={mockOnClose}
        onDelegationChange={mockOnDelegationChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Manage Delegation')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search people…')).toBeInTheDocument();
      expect(screen.getByText('Delegate')).toBeInTheDocument();
    });
  });

  it('should render revoke mode when delegation exists', async () => {
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
      <ManageDelegationModal
        open={true}
        onClose={mockOnClose}
        onDelegationChange={mockOnDelegationChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Manage Delegation')).toBeInTheDocument();
      expect(screen.getByText('You currently delegate all polls to Alice')).toBeInTheDocument();
      expect(screen.getByText('Revoke delegation')).toBeInTheDocument();
    });
  });

  it('should show search results when typing', async () => {
    vi.mocked(api.getMyDelegation).mockResolvedValue({});
    vi.mocked(api.searchUsers).mockResolvedValue([
      { id: 'user-1', name: 'Alice' },
      { id: 'user-2', name: 'Bob' }
    ]);

    render(
      <ManageDelegationModal
        open={true}
        onClose={mockOnClose}
        onDelegationChange={mockOnDelegationChange}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search people…');
    fireEvent.change(searchInput, { target: { value: 'alice' } });

    await waitFor(() => {
      expect(api.searchUsers).toHaveBeenCalledWith('alice');
    });

    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('Bob')).toBeInTheDocument();
    });
  });

  it('should enable delegate button when user is selected', async () => {
    vi.mocked(api.getMyDelegation).mockResolvedValue({});
    vi.mocked(api.searchUsers).mockResolvedValue([
      { id: 'user-1', name: 'Alice' }
    ]);

    render(
      <ManageDelegationModal
        open={true}
        onClose={mockOnClose}
        onDelegationChange={mockOnDelegationChange}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search people…');
    fireEvent.change(searchInput, { target: { value: 'alice' } });

    await waitFor(() => {
      const aliceButton = screen.getByText('Alice');
      fireEvent.click(aliceButton);
    });

    const delegateButton = screen.getByText('Delegate');
    expect(delegateButton).not.toBeDisabled();
  });

  it('should call createDelegation when delegate button is clicked', async () => {
    vi.mocked(api.getMyDelegation).mockResolvedValue({});
    vi.mocked(api.searchUsers).mockResolvedValue([
      { id: 'user-1', name: 'Alice' }
    ]);
    vi.mocked(api.createDelegation).mockResolvedValue();

    render(
      <ManageDelegationModal
        open={true}
        onClose={mockOnClose}
        onDelegationChange={mockOnDelegationChange}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search people…');
    fireEvent.change(searchInput, { target: { value: 'alice' } });

    await waitFor(() => {
      const aliceButton = screen.getByText('Alice');
      fireEvent.click(aliceButton);
    });

    const delegateButton = screen.getByText('Delegate');
    fireEvent.click(delegateButton);

    await waitFor(() => {
      expect(api.createDelegation).toHaveBeenCalledWith({
        to_user_id: 'user-1',
        scope: 'global'
      });
    });
  });

  it('should call removeDelegation when revoke button is clicked', async () => {
    const mockDelegation = {
      global: {
        to_user_id: 'user-123',
        to_user_name: 'Alice',
        active: true,
        chain: []
      }
    };

    vi.mocked(api.getMyDelegation).mockResolvedValue(mockDelegation);
    vi.mocked(api.removeDelegation).mockResolvedValue();

    render(
      <ManageDelegationModal
        open={true}
        onClose={mockOnClose}
        onDelegationChange={mockOnDelegationChange}
      />
    );

    await waitFor(() => {
      const revokeButton = screen.getByText('Revoke delegation');
      fireEvent.click(revokeButton);
    });

    await waitFor(() => {
      expect(api.removeDelegation).toHaveBeenCalledWith({
        scope: 'global'
      });
    });
  });

  it('should close modal when close button is clicked', async () => {
    vi.mocked(api.getMyDelegation).mockResolvedValue({});

    render(
      <ManageDelegationModal
        open={true}
        onClose={mockOnClose}
        onDelegationChange={mockOnDelegationChange}
      />
    );

    await waitFor(() => {
      const closeButton = screen.getByLabelText('Close');
      fireEvent.click(closeButton);
    });

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should show error message when API call fails', async () => {
    vi.mocked(api.getMyDelegation).mockResolvedValue({});
    vi.mocked(api.searchUsers).mockResolvedValue([
      { id: 'user-1', name: 'Alice' }
    ]);
    vi.mocked(api.createDelegation).mockRejectedValue({
      message: 'Failed to create delegation'
    });

    render(
      <ManageDelegationModal
        open={true}
        onClose={mockOnClose}
        onDelegationChange={mockOnDelegationChange}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search people…');
    fireEvent.change(searchInput, { target: { value: 'alice' } });

    await waitFor(() => {
      const aliceButton = screen.getByText('Alice');
      fireEvent.click(aliceButton);
    });

    const delegateButton = screen.getByText('Delegate');
    fireEvent.click(delegateButton);

    await waitFor(() => {
      expect(screen.getByText('Failed to create delegation')).toBeInTheDocument();
    });
  });
});
