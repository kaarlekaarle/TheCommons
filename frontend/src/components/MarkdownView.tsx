import React, { useEffect, useRef } from 'react';

interface MarkdownViewProps {
  markdown: string;
}

// Enhanced markdown parser for our specific use case
function parseMarkdown(markdown: string): string {
  let html = markdown;
  
  // Headers with IDs
  html = html.replace(/^### (.*?)$/gm, '<h3 class="text-xl font-semibold mt-6 mb-3">$1</h3>');
  html = html.replace(/^## (.*?) \{#([^}]+)\}$/gm, '<h2 id="$2" class="text-2xl md:text-3xl font-semibold mt-12 mb-6 scroll-mt-24">$1</h2>');
  html = html.replace(/^## (.*?)$/gm, '<h2 id="$1" class="text-2xl md:text-3xl font-semibold mt-12 mb-6 scroll-mt-24">$1</h2>');
  html = html.replace(/^# (.*?)$/gm, '<h1 class="text-3xl md:text-4xl font-bold mb-6">$1</h1>');
  
  // Code blocks (must come before paragraphs)
  html = html.replace(/^```(\w+)?\n([\s\S]*?)\n```$/gm, '<pre class="bg-surface border border-border rounded-lg p-4 my-4 overflow-x-auto"><code class="text-sm text-muted">$2</code></pre>');
  html = html.replace(/`([^`]+)`/g, '<code class="bg-surface border border-border rounded px-1 py-0.5 text-sm text-muted">$1</code>');
  
  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-primary hover:text-primary/80 underline" target="_blank" rel="noopener noreferrer">$1</a>');
  
  // Bold text
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>');
  
  // Italic text
  html = html.replace(/\*(.*?)\*/g, '<em class="italic text-muted">$1</em>');
  
  // Blockquotes (must come before paragraphs)
  html = html.replace(/^> (.*?)$/gm, '<blockquote class="italic text-muted border-l-4 border-primary/30 pl-4 my-4">$1</blockquote>');
  
  // Lists - handle ordered lists first
  html = html.replace(/^(\d+)\. (.*?)$/gm, '<li class="mb-2" data-ordered="true">$2</li>');
  // Then unordered lists
  html = html.replace(/^- (.*?)$/gm, '<li class="mb-2" data-ordered="false">$1</li>');
  
  // Wrap consecutive list items
  html = html.replace(/(<li class="mb-2" data-ordered="[^"]*">.*?<\/li>)(\s*<li class="mb-2" data-ordered="[^"]*">.*?<\/li>)*/gs, (match) => {
    const items = match.match(/<li class="mb-2" data-ordered="[^"]*">.*?<\/li>/g);
    if (!items) return match;
    
    // Check if it's an ordered list (contains data-ordered="true")
    const isOrdered = items.some(item => item.includes('data-ordered="true"'));
    const tag = isOrdered ? 'ol' : 'ul';
    const classes = isOrdered ? 'space-y-4' : 'space-y-2';
    
    // Remove the data-ordered attributes
    const cleanItems = items.map(item => item.replace(/ data-ordered="[^"]*"/g, ''));
    
    return `<${tag} class="${classes} text-lg text-muted leading-relaxed mb-4">${cleanItems.join('')}</${tag}>`;
  });
  
  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr class="border-border my-8">');
  
  // Paragraphs (but not if already wrapped in other tags)
  html = html.replace(/^(?!<[h|o|u|b|p|q|d|a|c])(.*?)$/gm, '<p class="text-lg text-muted leading-relaxed mb-4">$1</p>');
  
  // Remove empty paragraphs
  html = html.replace(/<p class="text-lg text-muted leading-relaxed mb-4"><\/p>/g, '');
  
  // Clean up multiple newlines
  html = html.replace(/\n\s*\n/g, '\n');
  
  return html;
}

export default function MarkdownView({ markdown }: MarkdownViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      try {
        containerRef.current.innerHTML = parseMarkdown(markdown);
      } catch (error) {
        console.error('Error parsing markdown:', error);
        containerRef.current.innerHTML = '<p class="text-muted">Error rendering content</p>';
      }
    }
  }, [markdown]);

  return (
    <div 
      ref={containerRef}
      className="space-y-6 prose prose-invert max-w-none"
    >
      {/* Content will be inserted here by useEffect */}
    </div>
  );
}
