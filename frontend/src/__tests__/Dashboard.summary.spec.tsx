import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';

// Mock the API functions
jest.mock('../lib/api', () => ({
  listPolls: jest.fn(),
  getContentPrinciples: jest.fn(),
  getContentActions: jest.fn(),
  getSafeDelegationSummary: jest.fn(),
  setDelegation: jest.fn(),
  listLabels: jest.fn(),
}));

// Mock the telemetry
jest.mock('../api/delegationsApi', () => ({
  trackDelegationSummaryLoaded: jest.fn(),
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

// Mock TransparencyPanel
jest.mock('../components/delegations/TransparencyPanel', () => {
  return function MockTransparencyPanel() {
    return <div data-testid="transparency-panel">Transparency Panel</div>;
  };
});

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
    const { listPolls, getContentPrinciples, getContentActions, listLabels } = require('../lib/api');
    listPolls.mockResolvedValue([]);
    getContentPrinciples.mockResolvedValue([]);
    getContentActions.mockResolvedValue([]);
    listLabels.mockResolvedValue([]);
  });

  describe('Test A: Happy path', () => {
    it('shows summary UI when delegation summary is ok', async () => {
      const { getSafeDelegationSummary } = require('../lib/api');
      getSafeDelegationSummary.mockResolvedValue({
        ok: true,
        counts: { mine: 1, inbound: 0 },
        meta: { generated_at: '2025-01-01T00:00:00Z' }
      });

      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Your Delegations by Topic')).toBeInTheDocument();
      });

      // Should not show fallback text
      expect(screen.queryByText('Delegation summary unavailable')).not.toBeInTheDocument();
    });
  });

  describe('Test B: Fallback path', () => {
    it('shows fallback UI with retry button, transparency button, and trace id', async () => {
      const { getSafeDelegationSummary } = require('../lib/api');
      getSafeDelegationSummary.mockResolvedValue({
        ok: false,
        counts: { mine: 0, inbound: 0 },
        meta: { trace_id: 'abc123', generated_at: '2025-01-01T00:00:00Z' }
      });

      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Delegation summary unavailable')).toBeInTheDocument();
      });

      // Assert key elements are present
      expect(screen.getByText('Retry later or open Transparency')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Open Transparency' })).toBeInTheDocument();
      expect(screen.getByText('Trace: abc123')).toBeInTheDocument();
    });
  });
});
