import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ContentList from '../ContentList';
import type { PrincipleItem, ActionItem } from '../../../types/content';

const mockPrinciples: PrincipleItem[] = [
  {
    id: 'p-1',
    title: 'Test Principle 1',
    description: 'This is a test principle',
    tags: ['test', 'principle'],
    source: 'Test source'
  },
  {
    id: 'p-2',
    title: 'Test Principle 2',
    description: 'This is another test principle',
    tags: ['test'],
    source: 'Test source 2'
  }
];

const mockActions: ActionItem[] = [
  {
    id: 'a-1',
    title: 'Test Action 1',
    description: 'This is a test action',
    scope: 'city',
    tags: ['test', 'action'],
    source: 'Test source'
  }
];

describe('ContentList', () => {
  it('renders title and items correctly', () => {
    render(
      <ContentList
        title="Test Principles"
        items={mockPrinciples}
      />
    );

    expect(screen.getByText('Test Principles')).toBeInTheDocument();
    expect(screen.getByText('Test Principle 1')).toBeInTheDocument();
    expect(screen.getByText('Test Principle 2')).toBeInTheDocument();
    expect(screen.getByText('This is a test principle')).toBeInTheDocument();
    expect(screen.getByText('This is another test principle')).toBeInTheDocument();
  });

  it('renders tags correctly', () => {
    render(
      <ContentList
        title="Test Principles"
        items={mockPrinciples}
      />
    );

    expect(screen.getAllByText('test')).toHaveLength(2);
    expect(screen.getByText('principle')).toBeInTheDocument();
  });

  it('renders source information when not compact', () => {
    render(
      <ContentList
        title="Test Principles"
        items={mockPrinciples}
        compact={false}
      />
    );

    expect(screen.getByText('Source: Test source')).toBeInTheDocument();
    expect(screen.getByText('Source: Test source 2')).toBeInTheDocument();
  });

  it('does not render source information when compact', () => {
    render(
      <ContentList
        title="Test Principles"
        items={mockPrinciples}
        compact={true}
      />
    );

    expect(screen.queryByText('Source: Test source')).not.toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(
      <ContentList
        title="Test Principles"
        items={[]}
        loading={true}
      />
    );

    expect(screen.getByText('Test Principles')).toBeInTheDocument();
    // Should show skeleton loading elements
    const skeletonElements = document.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('shows error state', () => {
    render(
      <ContentList
        title="Test Principles"
        items={[]}
        error="Failed to load content"
      />
    );

    expect(screen.getByText('Test Principles')).toBeInTheDocument();
    expect(screen.getByText('Unable to load content')).toBeInTheDocument();
  });

  it('shows empty state with custom message', () => {
    render(
      <ContentList
        title="Test Principles"
        items={[]}
        emptyMessage="No principles available"
      />
    );

    expect(screen.getByText('Test Principles')).toBeInTheDocument();
    expect(screen.getByText('No principles available')).toBeInTheDocument();
  });

  it('shows default empty message when none provided', () => {
    render(
      <ContentList
        title="Test Principles"
        items={[]}
      />
    );

    expect(screen.getByText('Test Principles')).toBeInTheDocument();
    expect(screen.getByText('No items available')).toBeInTheDocument();
  });

  it('handles actions with scope correctly', () => {
    render(
      <ContentList
        title="Test Actions"
        items={mockActions}
      />
    );

    expect(screen.getByText('Test Action 1')).toBeInTheDocument();
    expect(screen.getByText('This is a test action')).toBeInTheDocument();
    expect(screen.getByText('action')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <ContentList
        title="Test Principles"
        items={mockPrinciples}
        className="custom-class"
      />
    );

    const container = document.querySelector('.gov-card.custom-class');
    expect(container).toBeInTheDocument();
  });
});
