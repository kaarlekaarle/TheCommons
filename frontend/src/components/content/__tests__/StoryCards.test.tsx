import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import StoryCards from '../StoryCards';
import type { StoryItem } from '../../../types/content';

const mockStories: StoryItem[] = [
  {
    id: 's-1',
    title: 'Test Story 1',
    summary: 'This is a test story summary',
    impact: 'Test impact',
    link: 'https://example.com'
  },
  {
    id: 's-2',
    title: 'Test Story 2',
    summary: 'This is another test story summary',
    impact: 'Another test impact'
  }
];

describe('StoryCards', () => {
  it('renders stories correctly', () => {
    render(<StoryCards stories={mockStories} />);

    expect(screen.getByText('Test Story 1')).toBeInTheDocument();
    expect(screen.getByText('Test Story 2')).toBeInTheDocument();
    expect(screen.getByText('This is a test story summary')).toBeInTheDocument();
    expect(screen.getByText('This is another test story summary')).toBeInTheDocument();
  });

  it('renders impact information', () => {
    render(<StoryCards stories={mockStories} />);

    expect(screen.getByText('Impact: Test impact')).toBeInTheDocument();
    expect(screen.getByText('Impact: Another test impact')).toBeInTheDocument();
  });

  it('renders link when provided', () => {
    render(<StoryCards stories={mockStories} />);

    const link = screen.getByRole('link', { name: /learn more/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'https://example.com');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('does not render link when not provided', () => {
    const storiesWithoutLink: StoryItem[] = [
      {
        id: 's-1',
        title: 'Test Story 1',
        summary: 'This is a test story summary',
        impact: 'Test impact'
      }
    ];

    render(<StoryCards stories={storiesWithoutLink} />);

    expect(screen.queryByText('Learn more')).not.toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<StoryCards stories={[]} loading={true} />);

    // Should show skeleton loading elements
    const skeletonElements = document.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('shows error state', () => {
    render(<StoryCards stories={[]} error="Failed to load stories" />);

    expect(screen.getByText('Unable to load stories')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<StoryCards stories={[]} />);

    expect(screen.getByText('No stories available')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<StoryCards stories={mockStories} className="custom-class" />);

    const container = document.querySelector('.custom-class');
    expect(container).toBeInTheDocument();
  });

  it('renders in grid layout', () => {
    render(<StoryCards stories={mockStories} />);

    const gridContainer = document.querySelector('.grid');
    expect(gridContainer).toBeInTheDocument();
    expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
  });

  it('handles stories without impact', () => {
    const storiesWithoutImpact: StoryItem[] = [
      {
        id: 's-1',
        title: 'Test Story 1',
        summary: 'This is a test story summary'
      }
    ];

    render(<StoryCards stories={storiesWithoutImpact} />);

    expect(screen.getByText('Test Story 1')).toBeInTheDocument();
    expect(screen.getByText('This is a test story summary')).toBeInTheDocument();
    expect(screen.queryByText(/Impact:/)).not.toBeInTheDocument();
  });
});
