import { render } from '@testing-library/react';
import { axe } from 'jest-axe';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import ProposalCard from '../../components/ProposalCard';

// Mock the flags
vi.mock('../../config/flags', () => ({
  flags: { labelsEnabled: false }
}));

const mockPoll = {
  id: 'test-poll-1',
  title: 'Test Proposal Title',
  description: 'This is a test proposal description that should be long enough to test line clamping.',
  decision_type: 'level_b' as const,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  created_by: 'test-user',
  is_active: true,
  labels: []
};

test('ProposalCard AA contrast', async () => {
  const { container } = render(
    <BrowserRouter>
      <ProposalCard poll={mockPoll} />
    </BrowserRouter>
  );
  
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});

test('ProposalCard with labels has no violations', async () => {
  const pollWithLabels = {
    ...mockPoll,
    labels: [
      { id: 'label-1', name: 'Test Label', slug: 'test-label' }
    ]
  };
  
  const { container } = render(
    <BrowserRouter>
      <ProposalCard poll={pollWithLabels} />
    </BrowserRouter>
  );
  
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
