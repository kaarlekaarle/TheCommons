import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useActiveSections } from '../hooks/useActiveSections';
import MarkdownView from '../components/MarkdownView';

interface TocItem {
  id: string;
  title: string;
}

export default function WhyTwoLevels() {
  const [tocItems, setTocItems] = useState<TocItem[]>([]);
  const [sectionIds, setSectionIds] = useState<string[]>([]);
  const [hasError, setHasError] = useState(false);
  const [markdownContent, setMarkdownContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const { activeId } = useActiveSections(sectionIds);

  // Load markdown content
  useEffect(() => {
    const loadMarkdown = async () => {
      try {
        setIsLoading(true);
        const module = await import('../../docs/two-levels.md?raw');
        const content = module.default;
        setMarkdownContent(content);
        setHasError(false);
      } catch (error) {
        setHasError(true);
        if (import.meta.env.DEV) {
          console.error('Failed to load markdown content:', error);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadMarkdown();
  }, []);

  // Extract TOC items from markdown content
  useEffect(() => {
    if (!markdownContent || hasError) return;

    try {
      const lines = markdownContent.split('\n');
      const items: TocItem[] = [];
      const ids: string[] = [];
      
      lines.forEach(line => {
        const h2Match = line.match(/^## (.*?) \{#([^}]+)\}$/);
        if (h2Match) {
          const title = h2Match[1];
          const id = h2Match[2];
          items.push({ id, title });
          ids.push(id);
        }
      });
      
      setTocItems(items);
      setSectionIds(ids);
    } catch (error) {
      setHasError(true);
      if (import.meta.env.DEV) {
        console.error('Error processing markdown content:', error);
      }
    }
  }, [markdownContent, hasError]);

  const scrollTo = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-bg text-white min-h-screen">
        <header className="sticky top-0 z-20 bg-bg/80 backdrop-blur border-b border-border">
          <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
            <Link to="/" className="text-muted hover:text-white">← Back to Home</Link>
            <Link to="/auth?mode=register" className="bg-primary/90 hover:bg-primary text-white px-4 py-2 rounded-lg">Try The Commons</Link>
          </div>
        </header>

        <main className="max-w-3xl mx-auto px-6 py-10">
          <div className="text-center space-y-6">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="text-lg text-muted">Loading content...</p>
          </div>
        </main>

        <footer className="px-6 py-10 text-center text-sm text-muted border-t border-border">
          © {new Date().getFullYear()} The Commons — Two‑Level Decision Thinking
        </footer>
      </div>
    );
  }

  // Error fallback component
  if (hasError) {
    return (
      <div className="bg-bg text-white min-h-screen">
        <header className="sticky top-0 z-20 bg-bg/80 backdrop-blur border-b border-border">
          <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
            <Link to="/" className="text-muted hover:text-white">← Back to Home</Link>
            <Link to="/auth?mode=register" className="bg-primary/90 hover:bg-primary text-white px-4 py-2 rounded-lg">Try The Commons</Link>
          </div>
        </header>

        <main className="max-w-3xl mx-auto px-6 py-10">
          <div className="text-center space-y-6">
            <div className="text-6xl mb-4">⚠️</div>
            <h1 className="text-2xl font-bold text-white mb-4">
              Content temporarily unavailable
            </h1>
            <p className="text-lg text-muted leading-relaxed">
              Please check back later. We're working to restore the content.
            </p>
            <div className="mt-8">
              <Link 
                to="/" 
                className="bg-primary/90 hover:bg-primary text-white px-6 py-3 rounded-lg inline-block"
              >
                Return to Home
              </Link>
            </div>
          </div>
        </main>

        <footer className="px-6 py-10 text-center text-sm text-muted border-t border-border">
          © {new Date().getFullYear()} The Commons — Two‑Level Decision Thinking
        </footer>
      </div>
    );
  }

  return (
    <div className="bg-bg text-white min-h-screen">
      <header className="sticky top-0 z-20 bg-bg/80 backdrop-blur border-b border-border">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link to="/" className="text-muted hover:text-white">← Back to Home</Link>
          <div className="flex items-center space-x-4">
            {import.meta.env.DEV && (
              <a 
                href="https://github.com/your-repo/The-Commons-2nd/edit/main/docs/two-levels.md" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm text-muted hover:text-white underline"
              >
                Edit this page
              </a>
            )}
            <Link to="/auth?mode=register" className="bg-primary/90 hover:bg-primary text-white px-4 py-2 rounded-lg">Try The Commons</Link>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10 space-y-12">
        {/* Table of contents */}
        <div className="bg-surface border border-border rounded-xl p-6">
          <h2 className="text-2xl md:text-3xl font-semibold mb-4">Table of Contents</h2>
          <nav className="space-y-2">
            {tocItems.map((item) => {
              const isActive = activeId === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => scrollTo(item.id)}
                  className={`block w-full text-left transition-colors ${
                    isActive 
                      ? "text-white font-medium" 
                      : "text-muted hover:text-white"
                  }`}
                  aria-current={isActive ? "true" : undefined}
                >
                  {item.title}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Markdown content */}
        <MarkdownView markdown={markdownContent} />
      </main>

              <footer className="px-6 py-10 text-center text-sm text-muted border-t border-border">
          © {new Date().getFullYear()} The Commons — Two‑Level Decision Thinking
        </footer>
    </div>
  );
}
