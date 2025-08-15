import React, { useState } from 'react';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Card from '../ui/Card';
import { principlesDocCopy } from '../../copy/principlesDoc';

interface CommunityDocumentProps {
  content: string;
  loading?: boolean;
}

export default function CommunityDocument({ content, loading = false }: CommunityDocumentProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-6 bg-gray-200 rounded w-32"></div>
            <div className="h-5 bg-emerald-200 rounded-full w-24"></div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </Card>
    );
  }

  const lines = content.split('\n');
  const shouldShowReadMore = lines.length > 10;
  const displayContent = isExpanded ? content : lines.slice(0, 10).join('\n');

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-4">
        <h3 className="text-xl font-semibold text-gray-900">
          {principlesDocCopy.communityDocTitle}
        </h3>
        <Badge variant="secondary" className="bg-emerald-50 text-emerald-700">
          {principlesDocCopy.livingPill}
        </Badge>
      </div>

      <div className="prose prose-gray max-w-none">
        <div className="whitespace-pre-line text-gray-800">
          {displayContent}
        </div>
      </div>

      {shouldShowReadMore && (
        <Button
          variant="ghost"
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-4 px-0 text-blue-600 hover:text-blue-700"
          aria-expanded={isExpanded}
        >
          {isExpanded ? principlesDocCopy.readLess : principlesDocCopy.readMore}
        </Button>
      )}
    </Card>
  );
}
