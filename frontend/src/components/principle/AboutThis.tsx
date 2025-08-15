import { useState } from 'react';
import { ExternalLink, Plus } from 'lucide-react';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Card from '../ui/Card';
import { principlesCopy } from '../../copy/principles';

interface PrincipleSource {
  id: string;
  title: string;
  org?: string;
  year?: number;
  url: string;
  summary?: string;
  stance?: 'supports' | 'questions' | 'mixed';
}

interface AboutThisProps {
  sources: PrincipleSource[];
  loading?: boolean;
  onSuggestSource?: () => void;
}

export default function AboutThis({
  sources,
  loading = false,
  onSuggestSource
}: AboutThisProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  if (loading) {
    return (
      <Card className="p-6" data-testid="about-this">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-24 bg-gray-200 rounded"></div>
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="border rounded-lg p-4 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/3"></div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  const getStanceBadge = (stance?: string) => {
    const config = {
      supports: { label: principlesCopy.about.stance.supports, className: 'bg-green-100 text-green-800 border-green-200' },
      questions: { label: principlesCopy.about.stance.questions, className: 'bg-red-100 text-red-800 border-red-200' },
      mixed: { label: principlesCopy.about.stance.mixed, className: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
      unknown: { label: 'Unknown', className: 'bg-gray-100 text-gray-800 border-gray-200' }
    };

    const stanceKey = stance || 'unknown';
    const badgeConfig = config[stanceKey as keyof typeof config] || config.unknown;

    return (
      <Badge variant="default" className={badgeConfig.className}>
        {badgeConfig.label}
      </Badge>
    );
  };

  const handleSuggestSource = () => {
    setIsModalOpen(true);
    onSuggestSource?.();
    // Analytics: principles_source_suggested
    console.log('principles_source_suggested', { principleId: 'current' });
  };

  return (
    <Card className="p-6" data-testid="about-this">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {principlesCopy.about.heading}
        </h3>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleSuggestSource}
          className="flex items-center gap-1"
        >
          <Plus className="w-3 h-3" />
          {principlesCopy.about.suggest}
        </Button>
      </div>

      {sources.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-600 mb-4">{principlesCopy.evidenceEmpty}</p>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleSuggestSource}
          >
            {principlesCopy.about.suggest}
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {sources.map((source) => (
            <div
              key={source.id}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                >
                  {source.title}
                  <ExternalLink className="w-3 h-3 inline ml-1" />
                </a>
                {getStanceBadge(source.stance)}
              </div>

              <div className="text-sm text-gray-600 mb-2">
                {source.org && source.year && `${source.org}, ${source.year}`}
                {source.org && !source.year && source.org}
                {!source.org && source.year && source.year.toString()}
              </div>

              {source.summary ? (
                <p className="text-gray-700 text-sm leading-relaxed line-clamp-3">
                  {source.summary}
                </p>
              ) : (
                <div className="text-sm text-gray-500">
                  {principlesCopy.about.noSummary}
                  <button
                    onClick={handleSuggestSource}
                    className="text-blue-600 hover:text-blue-800 font-medium ml-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                  >
                    Suggest one
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Simple modal for suggesting sources */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {principlesCopy.about.suggest}
            </h3>
            <p className="text-gray-600 mb-4">
              This feature is coming soon. For now, you can suggest sources through the revision composer.
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="secondary"
                onClick={() => setIsModalOpen(false)}
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
