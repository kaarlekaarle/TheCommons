import { useState } from 'react';
import Badge from '../ui/Badge';
import Card from '../ui/Card';
import { principlesCopy } from '../../copy/principles';

interface CommunityDocumentProps {
  content: string;
  loading?: boolean;
}

export default function CommunityDocument({ content, loading = false }: CommunityDocumentProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (loading) {
    return (
      <Card className="p-6 border-t-4 border-t-blue-500/70" data-testid="community-doc-card">
        <div className="animate-pulse space-y-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-20 bg-gray-200 rounded"></div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </Card>
    );
  }

  const displayContent = isExpanded ? content : content.slice(0, 300);
  const needsExpansion = content.length > 300;

  return (
    <Card
      className="p-6 border-t-4 border-t-blue-500/70 shadow-md"
      data-testid="community-doc-card"
    >
      <div className="flex items-center gap-2 mb-4">
        <Badge variant="default" className="bg-blue-100 text-blue-800 border-blue-200">
          {principlesCopy.livingLabel}
        </Badge>
      </div>

      <div className="prose prose-gray max-w-none">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {principlesCopy.communityDoc.title}
        </h2>

        <div className="text-gray-700 leading-relaxed">
          {displayContent}
          {needsExpansion && !isExpanded && '...'}
        </div>

        {needsExpansion && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-4 text-blue-600 hover:text-blue-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
          >
            {isExpanded ? 'Show less' : principlesCopy.communityDoc.readMore}
          </button>
        )}
      </div>
    </Card>
  );
}
