import React from 'react';
import { ExternalLink } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import { principlesDocCopy } from '../../copy/principlesDoc';

interface EvidenceItem {
  title: string;
  source: string;
  year: number;
  url: string;
}

interface EvidencePanelProps {
  evidence: EvidenceItem[];
  onSuggestSource: () => void;
  loading?: boolean;
}

export default function EvidencePanel({ evidence, onSuggestSource, loading = false }: EvidencePanelProps) {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-24 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
          <div className="h-9 bg-gray-200 rounded w-32 mt-4"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {principlesDocCopy.evidenceTitle}
      </h3>

      {evidence.length === 0 ? (
        <div className="text-center py-4">
          <p className="text-gray-600 mb-4">
            {principlesDocCopy.evidenceEmpty}
          </p>
          <Button
            variant="outline"
            onClick={onSuggestSource}
            className="w-full"
          >
            {principlesDocCopy.suggestSource}
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="space-y-3">
            {evidence.map((item, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded-lg">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex items-start gap-2 text-blue-600 hover:text-blue-700 underline decoration-blue-300 hover:decoration-blue-400 underline-offset-2"
                  onClick={() => {
                    // Analytics tracking could go here
                    console.log('Evidence link clicked:', item.title);
                  }}
                >
                  <div className="flex-1">
                    <div className="font-medium">{item.title}</div>
                    <div className="text-sm text-gray-600">
                      {item.source}, {item.year}
                    </div>
                  </div>
                  <ExternalLink className="w-4 h-4 flex-shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                </a>
              </div>
            ))}
          </div>

          <Button
            variant="outline"
            onClick={onSuggestSource}
            className="w-full"
          >
            {principlesDocCopy.suggestSource}
          </Button>
        </div>
      )}
    </Card>
  );
}
