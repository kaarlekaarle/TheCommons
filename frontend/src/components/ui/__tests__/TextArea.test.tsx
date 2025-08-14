import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TextArea from '../TextArea';

// Mock requestAnimationFrame
const mockRequestAnimationFrame = vi.fn((callback) => {
  callback();
  return 1;
});

const mockCancelAnimationFrame = vi.fn();

Object.defineProperty(window, 'requestAnimationFrame', {
  value: mockRequestAnimationFrame,
  writable: true,
});

Object.defineProperty(window, 'cancelAnimationFrame', {
  value: mockCancelAnimationFrame,
  writable: true,
});

describe('TextArea', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders as a controlled component', () => {
    const handleChange = vi.fn();
    render(
      <TextArea
        value="test value"
        onChange={handleChange}
        placeholder="Enter text"
      />
    );

    const textarea = screen.getByPlaceholderText('Enter text');
    expect(textarea).toHaveValue('test value');
  });

  it('calls onChange when value changes', () => {
    const handleChange = vi.fn();
    render(
      <TextArea
        value=""
        onChange={handleChange}
        placeholder="Enter text"
      />
    );

    const textarea = screen.getByPlaceholderText('Enter text');
    fireEvent.change(textarea, { target: { value: 'new value' } });

    expect(handleChange).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'change',
      })
    );
  });

  it('applies custom className', () => {
    render(
      <TextArea
        value=""
        onChange={vi.fn()}
        className="custom-class"
      />
    );

    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('custom-class');
  });

  it('forwards ref correctly', () => {
    const ref = vi.fn();
    render(
      <TextArea
        value=""
        onChange={vi.fn()}
        ref={ref}
      />
    );

    expect(ref).toHaveBeenCalledWith(expect.any(HTMLTextAreaElement));
  });

  it('sets default rows to 3', () => {
    render(
      <TextArea
        value=""
        onChange={vi.fn()}
      />
    );

    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('rows', '3');
  });

  it('allows custom rows', () => {
    render(
      <TextArea
        value=""
        onChange={vi.fn()}
        rows={5}
      />
    );

    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveAttribute('rows', '5');
  });

  it('applies default styling classes', () => {
    render(
      <TextArea
        value=""
        onChange={vi.fn()}
      />
    );

    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveClass('p-3', 'border', 'rounded-lg', 'focus:ring-2', 'focus:ring-primary/20', 'focus:border-primary', 'transition-colors', 'placeholder-gray-500');
  });

  it('forwards additional props', () => {
    render(
      <TextArea
        value=""
        onChange={vi.fn()}
        data-testid="custom-textarea"
        maxLength={100}
      />
    );

    const textarea = screen.getByTestId('custom-textarea');
    expect(textarea).toHaveAttribute('maxLength', '100');
  });

  it('handles disabled state', () => {
    render(
      <TextArea
        value=""
        onChange={vi.fn()}
        disabled
      />
    );

    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeDisabled();
  });

  it('handles placeholder text', () => {
    render(
      <TextArea
        value=""
        onChange={vi.fn()}
        placeholder="Enter your thoughts here"
      />
    );

    const textarea = screen.getByPlaceholderText('Enter your thoughts here');
    expect(textarea).toBeInTheDocument();
  });
});
