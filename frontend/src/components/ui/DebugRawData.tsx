import { useState } from 'react';
import { ChevronDown, ChevronRight, Code } from 'lucide-react';

interface DebugRawDataProps {
  data: unknown;
  title?: string;
}

export default function DebugRawData({ data, title = 'Raw Data' }: DebugRawDataProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Only render in development mode when VITE_DEBUG_RAW is true
  if (import.meta.env.PROD || import.meta.env.VITE_DEBUG_RAW !== 'true') {
    return null;
  }

  return (
    <div className="mt-8 border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-surface hover:bg-surface/80 transition-colors flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <Code className="w-4 h-4 text-muted" />
          <span className="text-sm font-medium text-muted">{title}</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-muted" />
        ) : (
          <ChevronRight className="w-4 h-4 text-muted" />
        )}
      </button>
      
      {isExpanded && (
        <div className="border-t border-border">
          <pre className="p-4 bg-bg text-xs text-muted overflow-x-auto max-h-96 overflow-y-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
