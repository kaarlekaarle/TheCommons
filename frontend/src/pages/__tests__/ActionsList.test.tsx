import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect } from 'vitest';
import ActionsList from '../ActionsList';

// Mock the ProposalGrid component
vi.mock('../../components/ProposalGrid', () => ({
  default: function MockProposalGrid({ title, decisionType, emptyTitle, emptySubtitle, ctaLabel, pageDescription }: { title: string; decisionType: string; emptyTitle: string; emptySubtitle: string; ctaLabel: string; pageDescription: string }) {
    return (
      <div data-testid="proposal-grid">
        <h1>{title}</h1>
        <p>Decision Type: {decisionType}</p>
        <p>Empty Title: {emptyTitle}</p>
        <p>Empty Subtitle: {emptySubtitle}</p>
        <p>CTA Label: {ctaLabel}</p>
        <p>Page Description: {pageDescription}</p>
      </div>
    );
  }
}));

describe('ActionsList', () => {
  it('renders with correct props for Level B proposals', () => {
    render(
      <BrowserRouter>
        <ActionsList />
      </BrowserRouter>
    );

    expect(screen.getByText('Actions')).toBeInTheDocument();
    expect(screen.getByText('Decision Type: level_b')).toBeInTheDocument();
    expect(screen.getByText('Empty Title: No actions yet')).toBeInTheDocument();
    expect(screen.getByText('Empty Subtitle: Be the first to propose a concrete action for your community.')).toBeInTheDocument();
    expect(screen.getByText('CTA Label: Propose an Action')).toBeInTheDocument();
    expect(screen.getByText('Page Description: Concrete choices we can act on now.')).toBeInTheDocument();
  });
});
