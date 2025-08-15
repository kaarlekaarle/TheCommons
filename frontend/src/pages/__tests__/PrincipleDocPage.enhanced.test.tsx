import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ToasterProvider } from '../../components/ui/Toaster';
import { vi } from 'vitest';
import PrincipleDocPage from '../PrincipleDocPage';
import * as api from '../../lib/api';

// Mock the flags to enable enhanced features
vi.mock('../../config/flags', () => ({
  flags: {
    principlesDocEnabled: true,
    principlesDocMode: true,
    compassEnabled: true,
    labelsEnabled: true
  }
}));

// Mock the API calls
vi.mock('../../lib/api');

const mockPoll = {
  id: 'test-1',
  title: 'Test Principle',
  description: 'Test description',
  longform_main: 'This is a comprehensive community document that outlines our approach to Level A principles.',
  extra: {
    counter_body: 'This counter-document presents an alternative perspective on the community approach.',
    evidence: [
      {
        title: 'Vision Zero framework',
        source: 'WHO',
        year: 2023,
        url: 'https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries',
        summary: 'Comprehensive framework for road safety',
        stance: 'supports'
      }
    ]
  },
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

test('renders enhanced principle page with proper layout', async () => {
  vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
  vi.mocked(api.listComments).mockResolvedValue({ comments: [] });

  renderWithRouter(<PrincipleDocPage />);

  // Wait for loading to complete and check that the page renders with enhanced features
  expect(await screen.findByText('Test Principle', {}, { timeout: 5000 })).toBeInTheDocument();

  // Check for enhanced components
  expect(screen.getByTestId('community-doc-card')).toBeInTheDocument();
  expect(screen.getByTestId('counter-doc-card')).toBeInTheDocument();
  expect(screen.getByTestId('revision-composer')).toBeInTheDocument();
  expect(screen.getByTestId('about-this')).toBeInTheDocument();

  // Check for tab switcher
  expect(screen.getByTestId('revisions-tab')).toBeInTheDocument();
  expect(screen.getByTestId('discussion-tab')).toBeInTheDocument();

  // Check for enhanced copy
  expect(screen.getByText('Living document')).toBeInTheDocument();
  expect(screen.getByText('Community document')).toBeInTheDocument();
  expect(screen.getByText('Counter-document')).toBeInTheDocument();
});

test('composer target toggles update CTA label', async () => {
  vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
  vi.mocked(api.listComments).mockResolvedValue({ comments: [] });

  renderWithRouter(<PrincipleDocPage />);

  // Wait for page to load
  await screen.findByText('Test Principle', {}, { timeout: 5000 });

  // Check initial CTA
  expect(screen.getByText('Post revision to Community doc')).toBeInTheDocument();

  // Click counter target
  const counterButton = screen.getByText('Counter');
  counterButton.click();

  // Check updated CTA
  expect(screen.getByText('Post addition to Counter-doc')).toBeInTheDocument();
});

test('tabs switch content and fire analytics', async () => {
  vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
  vi.mocked(api.listComments).mockResolvedValue({ comments: [] });

  const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

  renderWithRouter(<PrincipleDocPage />);

  // Wait for page to load
  await screen.findByText('Test Principle', {}, { timeout: 5000 });

  // Click discussion tab
  const discussionTab = screen.getByTestId('discussion-tab');
  discussionTab.click();

  // Check that analytics was fired
  expect(consoleSpy).toHaveBeenCalledWith('principles_view_switched', { view: 'discussion' });

  consoleSpy.mockRestore();
});
