import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ToasterProvider } from '../../components/ui/Toaster';
import { vi } from 'vitest';
import ProposalDetail from '../ProposalDetail';
import * as api from '../../lib/api';

// Mock the flags to enable compass
vi.mock('../../config/flags', () => ({
  flags: {
    principlesDocMode: true,
    compassEnabled: true,
    labelsEnabled: true
  }
}));

// Mock the API calls
vi.mock('../../lib/api');

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'ai-edu-001' })
  };
});

const mockPoll = {
        id: 'ai-edu-001',
  title: 'Test Principle',
  description: 'Test description',
  decision_type: 'level_a' as const,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  is_active: true,
  created_by: 'test-user',
  labels: []
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

test('redirects level_a proposals to compass when enabled', async () => {
  vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
  vi.mocked(api.getPollOptions).mockResolvedValue([]);
  vi.mocked(api.getMyVoteForPoll).mockResolvedValue(null);
  vi.mocked(api.getResults).mockResolvedValue(null);
  vi.mocked(api.getMyDelegation).mockResolvedValue(null);

  renderWithRouter(<ProposalDetail />);

  // Wait a bit for the component to process and redirect
  await new Promise(resolve => setTimeout(resolve, 100));

  // The redirect should happen after the poll data is loaded
      expect(mockNavigate).toHaveBeenCalledWith('/compass/ai-edu-001', { replace: true });
});
