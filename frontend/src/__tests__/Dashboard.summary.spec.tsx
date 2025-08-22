import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import * as api from '../lib/api';

// Mock the API functions
jest.mock('../lib/api', () => ({
  listPolls: jest.fn(),
  getContentPrinciples: jest.fn(),
  getContentActions: jest.fn(),
  getSafeDelegationSummary: jest.fn(),
  setDelegation: jest.fn(),
  listLabels: jest.fn(),
}));

// Mock the flags
jest.mock('../config/flags', () => ({
  flags: {
    labelsEnabled: true,
    useDemoContent: false,
  },
}));

// Mock the current user hook
jest.mock('../hooks/useCurrentUser', () => ({
  useCurrentUser: () => ({
    user: { id: 'test-user', username: 'testuser' },
    loading: false,
  }),
}));

// Mock the toast hook
jest.mock('../components/ui/useToast', () => ({
  useToast: () => ({
    error: jest.fn(),
    success: jest.fn(),
  }),
}));

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <Dashboard />
    </BrowserRouter>
  );
};

describe('Dashboard Summary', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Mock successful API calls for other data
    (api.listPolls as jest.Mock).mockResolvedValue([]);
    (api.getContentPrinciples as jest.Mock).mockResolvedValue([]);
    (api.getContentActions as jest.Mock).mockResolvedValue([]);
    (api.listLabels as jest.Mock).mockResolvedValue([]);
  });

  describe('Case A: Summary unavailable', () => {
    it('shows fallback text when summary is not ok', async () => {
      (api.getSafeDelegationSummary as jest.Mock).mockResolvedValue({
        ok: false,
        counts: { mine: 0, inbound: 0 },
        meta: { errors: ['test error'], generated_at: '2025-01-01T00:00:00Z' }
      });

      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Delegation summary unavailable')).toBeInTheDocument();
        expect(screen.getByText('Retry later or open Transparency')).toBeInTheDocument();
        expect(screen.getByText('Open Transparency')).toBeInTheDocument();
      });
    });
  });

  describe('Case B: Summary available', () => {
    it('shows summary content when summary is ok', async () => {
      (api.getSafeDelegationSummary as jest.Mock).mockResolvedValue({
        ok: true,
        counts: { mine: 1, inbound: 0 },
        global_delegate: {
          delegatee_username: 'testdelegate',
          active: true
        },
        per_label: [],
        meta: { generated_at: '2025-01-01T00:00:00Z' }
      });

      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Your Delegations by Topic')).toBeInTheDocument();
        expect(screen.getByText('Global Delegate:')).toBeInTheDocument();
        expect(screen.getByText('testdelegate')).toBeInTheDocument();
      });

      // Should not show fallback text
      expect(screen.queryByText('Delegation summary unavailable')).not.toBeInTheDocument();
    });
  });
});
