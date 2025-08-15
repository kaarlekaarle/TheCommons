import React from 'react';
import { ExternalLink } from 'lucide-react';
import { principlesCopy } from '../../copy/principles';

export default function FurtherLearning() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-2" data-testid="further-learning-title">
        {principlesCopy.furtherLearning.title}
      </h3>
      <p className="text-gray-600 text-sm mb-6" data-testid="further-learning-subtitle">
        {principlesCopy.furtherLearning.subtitle}
      </p>

      <div className="space-y-4">
        {principlesCopy.furtherLearning.sources.map((source, index) => (
          <div
            key={index}
            className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
            data-testid={`further-learning-source-${index}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 mb-1">
                  {source.title}
                </h4>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {source.description}
                </p>
              </div>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-4 text-blue-600 hover:text-blue-800 flex items-center gap-1 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/60 focus:ring-offset-2 rounded"
                data-testid={`further-learning-link-${index}`}
              >
                <ExternalLink className="w-3 h-3" />
                Read
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
