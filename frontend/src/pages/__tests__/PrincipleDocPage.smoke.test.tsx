import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ToasterProvider } from '../../components/ui/Toaster';
import PrincipleDocPage from '../PrincipleDocPage';
import * as api from '../../lib/api';
import { vi } from 'vitest';

// Mock the flags to enable doc mode
vi.mock('../../config/flags', () => ({
  flags: {
    principlesDocMode: true,
    compassEnabled: true
  }
}));

// Mock the API calls
vi.mock('../../lib/api');

const mockPoll = {
  id: 'test-poll',
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

test('renders principle doc page', async () => {
  vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
  vi.mocked(api.listComments).mockResolvedValue({ comments: [] });

  renderWithRouter(<PrincipleDocPage />);

  // Check that the page renders (shows loading state initially)
  expect(screen.getByText('Loading...')).toBeInTheDocument();
  expect(screen.getByText('Loading description...')).toBeInTheDocument();
});
