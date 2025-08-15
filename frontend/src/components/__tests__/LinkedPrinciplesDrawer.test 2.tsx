import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import LinkedPrinciplesDrawer from '../LinkedPrinciplesDrawer';
import { listPolls } from '../../lib/api';


// Mock the API
vi.mock('../../lib/api', () => ({
  listPolls: vi.fn(),
}));

// Mock the flags
vi.mock('../../config/flags', () => ({
  flags: {
    labelsEnabled: true,
  },
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
  };
});

const mockLabel = {
  id: 'label-1',
  name: 'Mobility',
  slug: 'mobility',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

const mockPrinciples = [
  {
    id: 'principle-1',
    title: 'Sustainable Transportation Policy',
    description: 'Establish comprehensive policy framework for sustainable transportation.',
    decision_type: 'level_a',
    direction_choice: 'Transportation Safety',
    created_by: 'user-1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    is_active: true,
    labels: [mockLabel]
  },
  {
    id: 'principle-2',
    title: 'Level A Principle (Placeholder)',
    description: 'Design streets to safely accommodate all users.',
    decision_type: 'level_a',
    direction_choice: 'Transportation Safety',
    created_by: 'user-2',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    is_active: true,
    labels: [mockLabel]
  }
];

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('LinkedPrinciplesDrawer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when open', () => {
    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={true}
        onClose={vi.fn()}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    expect(screen.getByText('Linked Principles')).toBeInTheDocument();
    expect(screen.getByText('Mobility')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={false}
        onClose={vi.fn()}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    expect(screen.queryByText('Linked Principles')).not.toBeInTheDocument();
  });

  it('fetches and displays linked principles', async () => {
    const mockListPolls = listPolls as vi.MockedFunction<typeof listPolls>;
    mockListPolls.mockResolvedValue(mockPrinciples);

    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={true}
        onClose={vi.fn()}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Sustainable Transportation Policy')).toBeInTheDocument();
      expect(screen.getByText('Level A Principle (Placeholder)')).toBeInTheDocument();
    });

    expect(mockListPolls).toHaveBeenCalledWith({
      decision_type: 'level_a',
      label: 'mobility',
      limit: 3
    });
  });

  it('shows loading state while fetching', () => {
    const mockListPolls = listPolls as vi.MockedFunction<typeof listPolls>;
    mockListPolls.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={true}
        onClose={vi.fn()}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    expect(screen.getByText('Loading principles...')).toBeInTheDocument();
  });

  it('shows error state when API fails', async () => {
    const mockListPolls = listPolls as vi.MockedFunction<typeof listPolls>;
    mockListPolls.mockRejectedValue(new Error('API Error'));

    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={true}
        onClose={vi.fn()}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('shows empty state when no principles found', async () => {
    const mockListPolls = listPolls as vi.MockedFunction<typeof listPolls>;
    mockListPolls.mockResolvedValue([]);

    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={true}
        onClose={vi.fn()}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No linked principles yet')).toBeInTheDocument();
      expect(screen.getByText('Create First Principle')).toBeInTheDocument();
    });
  });

  it('navigates to principle detail when clicked', async () => {
    const mockListPolls = listPolls as vi.MockedFunction<typeof listPolls>;
    mockListPolls.mockResolvedValue(mockPrinciples);
    const onClose = vi.fn();

    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={true}
        onClose={onClose}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Sustainable Transportation Policy')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Sustainable Transportation Policy'));

    expect(mockNavigate).toHaveBeenCalledWith('/proposals/principle-1');
    expect(onClose).toHaveBeenCalled();
  });

  it('navigates to explore all principles', async () => {
    const mockListPolls = listPolls as vi.MockedFunction<typeof listPolls>;
    mockListPolls.mockResolvedValue(mockPrinciples);
    const onClose = vi.fn();

    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={true}
        onClose={onClose}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Explore All Principles in Mobility')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Explore All Principles in Mobility'));

    expect(mockNavigate).toHaveBeenCalledWith('/principles?label=mobility');
    expect(onClose).toHaveBeenCalled();
  });

  it('closes drawer when backdrop is clicked', () => {
    const onClose = vi.fn();

    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={true}
        onClose={onClose}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    // Click on the backdrop div
    const backdrop = document.querySelector('.absolute.inset-0.bg-black.bg-opacity-50');
    expect(backdrop).toBeInTheDocument();
    fireEvent.click(backdrop!);

    expect(onClose).toHaveBeenCalled();
  });

  it('closes drawer when X button is clicked', () => {
    const onClose = vi.fn();

    renderWithRouter(
      <LinkedPrinciplesDrawer
        isOpen={true}
        onClose={onClose}
        label={mockLabel}
        currentPollId="current-poll"
      />
    );

    // Click on the close button (the button with the X icon)
    const closeButton = document.querySelector('button svg[aria-hidden="true"]')?.parentElement;
    expect(closeButton).toBeInTheDocument();
    fireEvent.click(closeButton!);

    expect(onClose).toHaveBeenCalled();
  });
});
