import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import LabelTile from '../LabelTile';

const mockLabel = {
  id: '1',
  name: 'Environment',
  slug: 'environment',
  is_active: true,
  created_at: '',
  updated_at: ''
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('LabelTile', () => {
  it('renders label name', () => {
    const onClick = vi.fn();
    
    renderWithRouter(
      <LabelTile
        label={mockLabel}
        onClick={onClick}
      />
    );

    expect(screen.getByText('Environment')).toBeInTheDocument();
  });

  it('renders count when provided', () => {
    const onClick = vi.fn();
    
    renderWithRouter(
      <LabelTile
        label={mockLabel}
        count={5}
        onClick={onClick}
      />
    );

    expect(screen.getByText('5 items')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    
    renderWithRouter(
      <LabelTile
        label={mockLabel}
        onClick={onClick}
      />
    );

    const tile = screen.getByRole('button');
    fireEvent.click(tile);

    expect(onClick).toHaveBeenCalledWith('environment');
  });

  it('calls onClick when Enter key is pressed', () => {
    const onClick = vi.fn();
    
    renderWithRouter(
      <LabelTile
        label={mockLabel}
        onClick={onClick}
      />
    );

    const tile = screen.getByRole('button');
    fireEvent.keyDown(tile, { key: 'Enter' });

    expect(onClick).toHaveBeenCalledWith('environment');
  });

  it('has proper accessibility attributes', () => {
    const onClick = vi.fn();
    
    renderWithRouter(
      <LabelTile
        label={mockLabel}
        count={5}
        onClick={onClick}
      />
    );

    const tile = screen.getByRole('button');
    expect(tile).toHaveAttribute('aria-label', 'Browse Environment (5 items)');
    expect(tile).toHaveAttribute('tabIndex', '0');
  });

  it('has proper accessibility attributes without count', () => {
    const onClick = vi.fn();
    
    renderWithRouter(
      <LabelTile
        label={mockLabel}
        onClick={onClick}
      />
    );

    const tile = screen.getByRole('button');
    expect(tile).toHaveAttribute('aria-label', 'Browse Environment');
  });
});
