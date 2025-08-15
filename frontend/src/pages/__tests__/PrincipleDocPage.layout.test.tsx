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

describe('PrincipleDocPage Layout', () => {
  beforeEach(() => {
    vi.mocked(api.getPoll).mockResolvedValue(mockPoll);
    vi.mocked(api.listComments).mockResolvedValue({ 
      comments: [],
      total: 0,
      limit: 20,
      offset: 0,
      has_more: false
    });
  });

  test('renders 3-track layout structure', async () => {
    renderWithRouter(<PrincipleDocPage />);

    // Wait for content to load
    await screen.findByTestId('main-question');

    // Check that the main container has the correct max-width
    const mainContainer = screen.getByRole('main');
    expect(mainContainer).toHaveClass('max-w-7xl');

    // Check that the content grid has 3 columns at lg breakpoint
    const contentGrid = mainContainer.querySelector('.grid.grid-cols-1.gap-6.lg\\:grid-cols-3');
    expect(contentGrid).toBeInTheDocument();

    // Check that the left section spans 2 columns
    const leftSection = contentGrid?.querySelector('.lg\\:col-span-2');
    expect(leftSection).toBeInTheDocument();

    // Check that the sidebar spans 1 column and is sticky
    const sidebar = contentGrid?.querySelector('.lg\\:col-span-1');
    expect(sidebar).toBeInTheDocument();
    expect(sidebar?.querySelector('.lg\\:sticky')).toBeInTheDocument();

    // Check that the perspectives are in a 2-column grid within the left section
    const perspectivesGrid = leftSection?.querySelector('.grid.grid-cols-1.gap-6.md\\:grid-cols-2');
    expect(perspectivesGrid).toBeInTheDocument();
  });

  test('renders correct content sections', async () => {
    renderWithRouter(<PrincipleDocPage />);

    // Wait for content to load
    await screen.findByTestId('main-question');

    // Check main question
    expect(screen.getByTestId('main-question')).toHaveTextContent(
      'What role do we want AI to play in education in the long run?'
    );

    // Check intro text
    expect(screen.getByTestId('intro-text')).toBeInTheDocument();

    // Check perspective cards
    expect(screen.getByTestId('perspective-card-primary')).toBeInTheDocument();
    expect(screen.getByTestId('perspective-card-alternate')).toBeInTheDocument();

    // Check conversation section
    expect(screen.getByTestId('conversation-title')).toBeInTheDocument();

    // Check further learning section
    expect(screen.getByTestId('further-learning-title')).toBeInTheDocument();

    // Verify no "Living document" text appears
    expect(screen.queryByText(/living document/i)).not.toBeInTheDocument();
  });

  test('perspective cards have correct button labels', async () => {
    renderWithRouter(<PrincipleDocPage />);

    // Wait for content to load
    await screen.findByTestId('main-question');

    // Check that both perspective cards have "I lean this way" buttons
    const alignButtons = screen.getAllByText('I lean this way');
    expect(alignButtons).toHaveLength(2);
  });

  test('sidebar is sticky at lg breakpoint', async () => {
    renderWithRouter(<PrincipleDocPage />);

    // Wait for content to load
    await screen.findByTestId('main-question');

    // Check that the sidebar has sticky positioning
    const sidebar = screen.getByRole('complementary');
    const stickyWrapper = sidebar.querySelector('.lg\\:sticky.lg\\:top-20');
    expect(stickyWrapper).toBeInTheDocument();
  });
});
