import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect } from 'vitest';
import PrinciplesList from '../PrinciplesList';

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

describe('PrinciplesList', () => {
  it('renders with correct props for Level A proposals', () => {
    render(
      <BrowserRouter>
        <PrinciplesList />
      </BrowserRouter>
    );

    expect(screen.getByText('Principles')).toBeInTheDocument();
    expect(screen.getByText('Decision Type: level_a')).toBeInTheDocument();
    expect(screen.getByText('Empty Title: No principles yet')).toBeInTheDocument();
    expect(screen.getByText('Empty Subtitle: Be the first to propose a long-term direction for your community.')).toBeInTheDocument();
    expect(screen.getByText('CTA Label: Propose a Principle')).toBeInTheDocument();
    expect(screen.getByText('Page Description: Shared north stars for our community (changed rarely).')).toBeInTheDocument();
  });
});
