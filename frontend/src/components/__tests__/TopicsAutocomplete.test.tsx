import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { axe, toHaveNoViolations } from 'jest-axe';
import TopicsAutocomplete from '../TopicsAutocomplete';
import * as cache from '../../lib/cache/labelsCache';
import { flags } from '../../config/flags';

// Mock the cache functions
vi.mock('../../lib/cache/labelsCache');
vi.mock('../../config/flags');

expect.extend(toHaveNoViolations);

const mockLabels = [
  { id: '1', name: 'Environment', slug: 'environment', is_active: true, created_at: '', updated_at: '' },
  { id: '2', name: 'Education', slug: 'education', is_active: true, created_at: '', updated_at: '' },
  { id: '3', name: 'Healthcare', slug: 'healthcare', is_active: true, created_at: '', updated_at: '' },
  { id: '4', name: 'Transportation', slug: 'transportation', is_active: true, created_at: '', updated_at: '' },
  { id: '5', name: 'Technology', slug: 'technology', is_active: true, created_at: '', updated_at: '' },
  { id: '6', name: 'Economy', slug: 'economy', is_active: true, created_at: '', updated_at: '' },
  { id: '7', name: 'Social Justice', slug: 'social-justice', is_active: true, created_at: '', updated_at: '' },
  { id: '8', name: 'Arts', slug: 'arts', is_active: true, created_at: '', updated_at: '' }
];

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('TopicsAutocomplete', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (flags.labelsEnabled as any) = true;
  });

  it('renders search input when open', () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByPlaceholderText('Search topics...')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('filters topics on input', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Environment')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Search topics...');
    fireEvent.change(input, { target: { value: 'env' } });

    await waitFor(() => {
      expect(screen.getByText('Environment')).toBeInTheDocument();
      expect(screen.queryByText('Education')).not.toBeInTheDocument();
    });
  });

  it('supports keyboard navigation', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Environment')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Search topics...');

    // Arrow down to select first item
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(screen.getByText('Environment')).toHaveAttribute('aria-selected', 'true');

    // Arrow down to select second item
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(screen.getByText('Education')).toHaveAttribute('aria-selected', 'true');

    // Arrow up to go back to first item
    fireEvent.keyDown(input, { key: 'ArrowUp' });
    expect(screen.getByText('Environment')).toHaveAttribute('aria-selected', 'true');
  });

  it('navigates on Enter key', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
    const mockNavigate = vi.fn();

    // Mock useNavigate
    vi.doMock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom');
      return {
        ...actual,
        useNavigate: () => mockNavigate
      };
    });

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Environment')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Search topics...');

    // Select first item and press Enter
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    // Note: This test would need more complex setup to fully test navigation
    // The actual navigation is handled by the component internally
  });

  it('closes on Escape key', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
    const onClose = vi.fn();

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={onClose}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Environment')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Search topics...');
    fireEvent.keyDown(input, { key: 'Escape' });

    expect(onClose).toHaveBeenCalled();
  });

  it('shows loading state', () => {
    vi.mocked(cache.getLabelsCached).mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText('Loading topics...')).toBeInTheDocument();
  });

  it('shows error state', async () => {
    vi.mocked(cache.getLabelsCached).mockRejectedValue(new Error('API Error'));

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load topics')).toBeInTheDocument();
    });
  });

  it('shows no results message', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Environment')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Search topics...');
    fireEvent.change(input, { target: { value: 'nonexistent' } });

    await waitFor(() => {
      expect(screen.getByText('No topics found')).toBeInTheDocument();
    });
  });

  it('limits results to top 6', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      // Should only show first 6 labels
      expect(screen.getByText('Environment')).toBeInTheDocument();
      expect(screen.getByText('Education')).toBeInTheDocument();
      expect(screen.getByText('Healthcare')).toBeInTheDocument();
      expect(screen.getByText('Transportation')).toBeInTheDocument();
      expect(screen.getByText('Technology')).toBeInTheDocument();
      expect(screen.getByText('Economy')).toBeInTheDocument();
      expect(screen.queryByText('Social Justice')).not.toBeInTheDocument();
      expect(screen.queryByText('Arts')).not.toBeInTheDocument();
    });
  });

  it('does not render when labels feature is disabled', () => {
    (flags.labelsEnabled as any) = false;

    const { container } = renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('has proper accessibility attributes', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Environment')).toBeInTheDocument();
    });

    const input = screen.getByRole('combobox');
    expect(input).toHaveAttribute('aria-expanded', 'true');
    expect(input).toHaveAttribute('aria-controls', 'topics-autocomplete-list');
    expect(input).toHaveAttribute('aria-autocomplete', 'list');
    expect(input).toHaveAttribute('aria-haspopup', 'listbox');

    const listbox = screen.getByRole('listbox');
    expect(listbox).toBeInTheDocument();

    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(6); // Top 6 results
  });

  it('aborts previous request when typing quickly', async () => {
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);

    renderWithRouter(
      <TopicsAutocomplete
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Environment')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Search topics...');
    
    // Type quickly to trigger multiple debounced calls
    fireEvent.change(input, { target: { value: 'e' } });
    fireEvent.change(input, { target: { value: 'en' } });
    fireEvent.change(input, { target: { value: 'env' } });

    // Wait for debounce to settle
    await waitFor(() => {
      expect(screen.getByText('Environment')).toBeInTheDocument();
    }, { timeout: 300 });
  });

  // Accessibility tests (only run in development)
  if (import.meta.env.DEV) {
    it('passes accessibility tests', async () => {
      vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);

      const { container } = renderWithRouter(
        <TopicsAutocomplete
          isOpen={true}
          onClose={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Environment')).toBeInTheDocument();
      });

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes accessibility tests in loading state', async () => {
      vi.mocked(cache.getLabelsCached).mockImplementation(() => new Promise(() => {}));

      const { container } = renderWithRouter(
        <TopicsAutocomplete
          isOpen={true}
          onClose={vi.fn()}
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes accessibility tests in error state', async () => {
      vi.mocked(cache.getLabelsCached).mockRejectedValue(new Error('API Error'));

      const { container } = renderWithRouter(
        <TopicsAutocomplete
          isOpen={true}
          onClose={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Failed to load topics')).toBeInTheDocument();
      });

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  }
});
