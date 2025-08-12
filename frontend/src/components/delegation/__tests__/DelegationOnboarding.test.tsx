import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import DelegationOnboarding from '../DelegationOnboarding';
import { trackOnboardingSeen } from '../../../lib/analytics';

// Mock analytics
vi.mock('../../../lib/analytics', () => ({
  trackOnboardingSeen: vi.fn(),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('DelegationOnboarding', () => {
  const mockOnClose = vi.fn();
  const mockOnLearnMore = vi.fn();
  const mockAnchorRef = {
    current: document.createElement('div'),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock getBoundingClientRect
    mockAnchorRef.current.getBoundingClientRect = vi.fn().mockReturnValue({
      left: 100,
      top: 50,
      bottom: 80,
      width: 200,
      height: 30,
    });
    // Mock window dimensions
    Object.defineProperty(window, 'innerWidth', { value: 1200 });
    Object.defineProperty(window, 'innerHeight', { value: 800 });
  });

  afterEach(() => {
    localStorageMock.clear();
  });

  it('should render onboarding tooltip with correct content', () => {
    render(
      <DelegationOnboarding
        anchorRef={mockAnchorRef}
        onClose={mockOnClose}
        onLearnMore={mockOnLearnMore}
      />
    );

    expect(screen.getByText('Trust someone to vote for you')).toBeInTheDocument();
    expect(screen.getByText(/If you're busy or unsure, you can delegate your vote to someone you trust. You're always in control./)).toBeInTheDocument();
    expect(screen.getByText('Got it')).toBeInTheDocument();
    expect(screen.getByText('Learn more')).toBeInTheDocument();
  });

  it('should have proper accessibility attributes', () => {
    render(
      <DelegationOnboarding
        anchorRef={mockAnchorRef}
        onClose={mockOnClose}
        onLearnMore={mockOnLearnMore}
      />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-labelledby', 'onboarding-title');
    expect(dialog).toHaveAttribute('aria-describedby', 'onboarding-body');
    
    expect(screen.getByLabelText('Close tooltip')).toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', () => {
    render(
      <DelegationOnboarding
        anchorRef={mockAnchorRef}
        onClose={mockOnClose}
        onLearnMore={mockOnLearnMore}
      />
    );

    const closeButton = screen.getByLabelText('Close tooltip');
    fireEvent.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should handle "Got it" button click', () => {
    render(
      <DelegationOnboarding
        anchorRef={mockAnchorRef}
        onClose={mockOnClose}
        onLearnMore={mockOnLearnMore}
      />
    );

    const gotItButton = screen.getByText('Got it');
    fireEvent.click(gotItButton);
    
    expect(localStorageMock.setItem).toHaveBeenCalledWith('commons.delegation.onboarded', 'true');
    expect(trackOnboardingSeen).toHaveBeenCalled();
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should handle "Learn more" button click', () => {
    render(
      <DelegationOnboarding
        anchorRef={mockAnchorRef}
        onClose={mockOnClose}
        onLearnMore={mockOnLearnMore}
      />
    );

    const learnMoreButton = screen.getByText('Learn more');
    fireEvent.click(learnMoreButton);
    
    expect(trackOnboardingSeen).toHaveBeenCalled();
    expect(mockOnLearnMore).toHaveBeenCalled();
  });

  it('should handle Escape key press', async () => {
    render(
      <DelegationOnboarding
        anchorRef={mockAnchorRef}
        onClose={mockOnClose}
        onLearnMore={mockOnLearnMore}
      />
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    
    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('should not render when anchor ref is null', () => {
    const nullAnchorRef = { current: null };
    
    const { container } = render(
      <DelegationOnboarding
        anchorRef={nullAnchorRef}
        onClose={mockOnClose}
        onLearnMore={mockOnLearnMore}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should position tooltip correctly', () => {
    render(
      <DelegationOnboarding
        anchorRef={mockAnchorRef}
        onClose={mockOnClose}
        onLearnMore={mockOnLearnMore}
      />
    );

    const tooltip = screen.getByRole('dialog');
    
    // Check that positioning styles are applied
    expect(tooltip).toHaveStyle('position: fixed');
    expect(tooltip).toHaveStyle('z-index: 50');
  });

  it('should handle window resize', async () => {
    render(
      <DelegationOnboarding
        anchorRef={mockAnchorRef}
        onClose={mockOnClose}
        onLearnMore={mockOnLearnMore}
      />
    );

    // Mock different window dimensions
    Object.defineProperty(window, 'innerHeight', { value: 400 });
    
    // Trigger resize event
    fireEvent.resize(window);
    
    // Should still render without errors
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
