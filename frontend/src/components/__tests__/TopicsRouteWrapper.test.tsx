import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import TopicsRouteWrapper from '../TopicsRouteWrapper';
import { flags } from '../../config/flags';
import * as cache from '../../lib/cache/labelsCache';

// Mock the flags and cache
vi.mock('../../config/flags');
vi.mock('../../lib/cache/labelsCache');

const mockLabels = [
  { id: '1', name: 'Environment', slug: 'environment', is_active: true, created_at: '', updated_at: '' }
];

const mockPopularLabels = [
  { id: '1', name: 'Environment', slug: 'environment', poll_count: 5 }
];

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('TopicsRouteWrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders TopicsHub when labels feature is enabled', async () => {
    (flags.labelsEnabled as any) = true;
    vi.mocked(cache.getLabelsCached).mockResolvedValue(mockLabels);
    vi.mocked(cache.getPopularLabelsCached).mockResolvedValue(mockPopularLabels);

    renderWithRouter(<TopicsRouteWrapper />);

    await waitFor(() => {
      expect(screen.getByText('Browse Topics')).toBeInTheDocument();
    });
  });

  it('renders TopicsDisabled when labels feature is disabled', () => {
    (flags.labelsEnabled as any) = false;

    renderWithRouter(<TopicsRouteWrapper />);

    expect(screen.getByText('Topics Are Not Available')).toBeInTheDocument();
    expect(screen.getByText(/The topics feature is not available right now/)).toBeInTheDocument();
  });

  it('shows navigation links in disabled state', () => {
    (flags.labelsEnabled as any) = false;

    renderWithRouter(<TopicsRouteWrapper />);

    expect(screen.getByText('Browse Principles')).toBeInTheDocument();
    expect(screen.getByText('Browse Actions')).toBeInTheDocument();
    expect(screen.getByText('Share Your Idea')).toBeInTheDocument();
  });
});
