import { render } from '@testing-library/react';
import { axe } from 'jest-axe';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import ProposalDetail from '../ProposalDetail';

// Mock the API calls
vi.mock('../../lib/api', () => ({
  getPoll: vi.fn().mockResolvedValue({
    id: 'test-poll-1',
    title: 'Test Proposal',
    description: 'This is a test proposal description',
    decision_type: 'level_b',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    labels: []
  }),
  getPollOptions: vi.fn().mockResolvedValue([]),
  getMyVoteForPoll: vi.fn().mockRejectedValue(new Error('Not authenticated')),
  getResults: vi.fn().mockRejectedValue(new Error('Not authenticated')),
  getMyDelegation: vi.fn().mockRejectedValue(new Error('Not authenticated'))
}));

// Mock the useParams hook
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal() as any;
  return {
    ...actual,
    useParams: () => ({ id: 'test-poll-1' }),
    useSearchParams: () => [new URLSearchParams(), vi.fn()]
  };
});

// Mock the useCurrentUser hook
vi.mock('../../hooks/useCurrentUser', () => ({
  useCurrentUser: () => ({ user: null, loading: false, error: null })
}));

// Mock the useToast hook
vi.mock('../../components/ui/useToast', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() })
}));

// Mock the flags
vi.mock('../../config/flags', () => ({
  flags: { labelsEnabled: false }
}));

test('ProposalDetail has no color-contrast violations', async () => {
  const { container } = render(
    <BrowserRouter>
      <ProposalDetail />
    </BrowserRouter>
  );
  
  const results = await axe(container, { 
    rules: { 
      'color-contrast': { enabled: true } 
    } 
  });
  
  expect(results).toHaveNoViolations();
});
