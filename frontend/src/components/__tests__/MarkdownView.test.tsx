import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MarkdownView from '../MarkdownView';

describe('MarkdownView', () => {
  it('renders H1 headings with correct classes', () => {
    const markdown = '# Main Heading';
    render(<MarkdownView markdown={markdown} />);
    
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveTextContent('Main Heading');
    expect(heading).toHaveClass('text-3xl', 'md:text-4xl', 'font-bold', 'mb-6');
  });

  it('renders H2 headings with IDs and correct classes', () => {
    const markdown = '## Subheading {#test-id}';
    render(<MarkdownView markdown={markdown} />);
    
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading).toHaveTextContent('Subheading');
    expect(heading).toHaveAttribute('id', 'test-id');
    expect(heading).toHaveClass('text-2xl', 'md:text-3xl', 'font-semibold', 'mt-12', 'mb-6', 'scroll-mt-24');
  });

  it('renders H2 headings without IDs', () => {
    const markdown = '## Subheading';
    render(<MarkdownView markdown={markdown} />);
    
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading).toHaveTextContent('Subheading');
    expect(heading).toHaveAttribute('id', 'Subheading');
    expect(heading).toHaveClass('text-2xl', 'md:text-3xl', 'font-semibold', 'mt-12', 'mb-6', 'scroll-mt-24');
  });

  it('renders H3 headings with correct classes', () => {
    const markdown = '### Sub-subheading';
    render(<MarkdownView markdown={markdown} />);
    
    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toHaveTextContent('Sub-subheading');
    expect(heading).toHaveClass('text-xl', 'font-semibold', 'mt-6', 'mb-3');
  });

  it('renders paragraphs with correct classes', () => {
    const markdown = 'This is a paragraph with some text.';
    render(<MarkdownView markdown={markdown} />);
    
    const paragraph = screen.getByText('This is a paragraph with some text.');
    expect(paragraph).toHaveClass('text-lg', 'text-muted', 'leading-relaxed', 'mb-4');
  });

  it('renders unordered lists with correct structure and classes', () => {
    const markdown = '- Item 1\n- Item 2\n- Item 3';
    render(<MarkdownView markdown={markdown} />);
    
    const lists = screen.getAllByRole('list');
    expect(lists).toHaveLength(1);
    const list = lists[0];
    expect(list).toHaveClass('space-y-2', 'text-lg', 'text-muted', 'leading-relaxed', 'mb-4');
    
    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(3);
    expect(items[0]).toHaveTextContent('Item 1');
    expect(items[1]).toHaveTextContent('Item 2');
    expect(items[2]).toHaveTextContent('Item 3');
    
    items.forEach(item => {
      expect(item).toHaveClass('mb-2');
    });
  });

  it('renders ordered lists with correct structure and classes', () => {
    const markdown = '1. First item\n2. Second item\n3. Third item';
    render(<MarkdownView markdown={markdown} />);
    
    const lists = screen.getAllByRole('list');
    expect(lists).toHaveLength(1);
    const list = lists[0];
    expect(list).toHaveClass('space-y-4', 'text-lg', 'text-muted', 'leading-relaxed', 'mb-4');
    
    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(3);
    expect(items[0]).toHaveTextContent('First item');
    expect(items[1]).toHaveTextContent('Second item');
    expect(items[2]).toHaveTextContent('Third item');
  });

  it('renders blockquotes with correct classes', () => {
    const markdown = '> This is a blockquote with important information.';
    render(<MarkdownView markdown={markdown} />);
    
    const blockquote = screen.getByText('This is a blockquote with important information.');
    expect(blockquote).toHaveClass('italic', 'text-muted', 'border-l-4', 'border-primary/30', 'pl-4', 'my-4');
  });

  it('renders bold text with correct classes', () => {
    const markdown = 'This text has **bold** parts.';
    render(<MarkdownView markdown={markdown} />);
    
    const boldText = screen.getByText('bold');
    expect(boldText).toHaveClass('font-semibold', 'text-white');
  });

  it('renders italic text with correct classes', () => {
    const markdown = 'This text has *italic* parts.';
    render(<MarkdownView markdown={markdown} />);
    
    const italicText = screen.getByText('italic');
    expect(italicText).toHaveClass('italic', 'text-muted');
  });

  it('renders inline code with correct classes', () => {
    const markdown = 'Use the `console.log()` function.';
    render(<MarkdownView markdown={markdown} />);
    
    const code = screen.getByText('console.log()');
    expect(code).toHaveClass('bg-surface', 'border', 'border-border', 'rounded', 'px-1', 'py-0.5', 'text-sm', 'text-muted');
  });

  it('renders code blocks with correct classes', () => {
    const markdown = '```javascript\nconst x = 1;\nconsole.log(x);\n```';
    render(<MarkdownView markdown={markdown} />);
    
    const preElements = screen.getAllByRole('generic');
    const pre = preElements.find(el => el.tagName === 'PRE');
    expect(pre).toHaveClass('bg-surface', 'border', 'border-border', 'rounded-lg', 'p-4', 'my-4', 'overflow-x-auto');
    
    // Check that code elements exist with correct classes
    const codeElements = screen.getAllByText(/const x = 1|console\.log\(x\)/);
    expect(codeElements.length).toBeGreaterThan(0);
    codeElements.forEach(code => {
      expect(code).toHaveClass('text-sm', 'text-muted');
    });
  });

  it('renders links with correct attributes and classes', () => {
    const markdown = 'Visit [The Commons](https://example.com) for more info.';
    render(<MarkdownView markdown={markdown} />);
    
    const link = screen.getByRole('link');
    expect(link).toHaveTextContent('The Commons');
    expect(link).toHaveAttribute('href', 'https://example.com');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(link).toHaveClass('text-primary', 'hover:text-primary/80', 'underline');
  });

  it('renders horizontal rules with correct classes', () => {
    const markdown = '---';
    render(<MarkdownView markdown={markdown} />);
    
    const hr = screen.getByRole('separator');
    expect(hr).toHaveClass('border-border', 'my-8');
  });

  it('strips {#id} tags from visible text but preserves ID attribute', () => {
    const markdown = '## Heading with ID {#my-id}';
    render(<MarkdownView markdown={markdown} />);
    
    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading).toHaveTextContent('Heading with ID');
    expect(heading).not.toHaveTextContent('{#my-id}');
    expect(heading).toHaveAttribute('id', 'my-id');
  });

  it('handles complex markdown with multiple elements', () => {
    const markdown = `# Main Title

## Section {#section-id}

This is a paragraph with **bold text** and *italic text*.

- List item 1
- List item 2

> Important quote here.

1. Numbered item
2. Another numbered item

---

Visit [The Commons](https://example.com) for more info.

Use \`console.log()\` for debugging.`;

    render(<MarkdownView markdown={markdown} />);
    
    // Check main heading
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Main Title');
    
    // Check section heading with ID
    const sectionHeading = screen.getByRole('heading', { level: 2 });
    expect(sectionHeading).toHaveTextContent('Section');
    expect(sectionHeading).toHaveAttribute('id', 'section-id');
    
    // Check paragraph
    expect(screen.getByText(/This is a paragraph with/)).toBeInTheDocument();
    
    // Check bold text
    expect(screen.getByText('bold text')).toHaveClass('font-semibold', 'text-white');
    
    // Check italic text
    expect(screen.getByText('italic text')).toHaveClass('italic', 'text-muted');
    
    // Check unordered list
    const lists = screen.getAllByRole('list');
    expect(lists.length).toBeGreaterThan(0);
    
    // Check blockquote
    expect(screen.getByText('Important quote here.')).toHaveClass('italic', 'text-muted');
    
    // Check link
    const link = screen.getByRole('link');
    expect(link).toHaveTextContent('The Commons');
    expect(link).toHaveAttribute('href', 'https://example.com');
    
    // Check inline code
    expect(screen.getByText('console.log()')).toHaveClass('bg-surface', 'border');
    
    // Check horizontal rule
    expect(screen.getByRole('separator')).toBeInTheDocument();
  });

  it('handles empty markdown gracefully', () => {
    const markdown = '';
    render(<MarkdownView markdown={markdown} />);
    
    // Just verify the component renders without error
    const containers = screen.getAllByRole('generic');
    expect(containers.length).toBeGreaterThan(0);
  });

  it('handles markdown with only whitespace', () => {
    const markdown = '   \n\n  \n';
    render(<MarkdownView markdown={markdown} />);
    
    // Just verify the component renders without error
    const containers = screen.getAllByRole('generic');
    expect(containers.length).toBeGreaterThan(0);
  });

  it('handles parsing errors gracefully', () => {
    // This test verifies that the component doesn't crash on malformed markdown
    const markdown = '```\nunclosed code block';
    render(<MarkdownView markdown={markdown} />);
    
    // Component should still render
    const containers = screen.getAllByRole('generic');
    expect(containers.length).toBeGreaterThan(0);
  });
});
