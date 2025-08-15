import React, { useState, useEffect, useRef } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import TextArea from '../ui/TextArea';
import { principlesCopy } from '../../copy/principles';

interface RevisionComposerProps {
  onSubmit: (body: string, target: 'main' | 'counter' | 'neutral') => void;
  isSubmitting?: boolean;
  initialTarget?: 'main' | 'counter' | 'neutral';
  placeholder?: string;
}

export default function RevisionComposer({
  onSubmit,
  isSubmitting = false,
  initialTarget = 'main',
  placeholder
}: RevisionComposerProps) {
  const [body, setBody] = useState('');
  const [target, setTarget] = useState<'main' | 'counter' | 'neutral'>(initialTarget);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const charCount = body.length;
  const isValid = charCount >= 240 && charCount <= 1000;

  useEffect(() => {
    if (initialTarget !== target) {
      setTarget(initialTarget);
    }
  }, [initialTarget]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid || isSubmitting) return;

    onSubmit(body, target);
    setBody('');
    setTarget('main');
  };

  const handleTargetChange = (newTarget: 'main' | 'counter' | 'neutral') => {
    setTarget(newTarget);
  };

  const getTargetConfig = (targetType: 'main' | 'counter' | 'neutral') => {
    switch (targetType) {
      case 'main': return principlesCopy.composer.target.community;
      case 'counter': return principlesCopy.composer.target.counter;
      case 'neutral': return principlesCopy.composer.target.neutral;
    }
  };

  const currentTargetConfig = getTargetConfig(target);

  return (
    <Card className="p-6" data-testid="revision-composer">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {principlesCopy.composer.heading}
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <TextArea
            ref={textareaRef}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder={placeholder || principlesCopy.composer.placeholder}
            className="min-h-[120px] resize-none w-full"
            disabled={isSubmitting}
            aria-describedby="char-count"
            onFocus={() => {
              // Analytics: principles_revision_opened
              console.log('principles_revision_opened', {
                principleId: 'current',
                target,
                length: charCount
              });
            }}
          />
          <div
            id="char-count"
            className={`text-sm mt-1 ${
              charCount > 1000 ? 'text-red-600' :
              charCount >= 240 ? 'text-gray-600' : 'text-gray-400'
            }`}
          >
            {charCount}/1000 • {principlesCopy.composer.helper}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {principlesCopy.composer.targetLabel}
          </label>
          <div className="flex gap-2">
            {(['main', 'counter', 'neutral'] as const).map((targetType) => {
              const config = getTargetConfig(targetType);
              const isSelected = target === targetType;

              return (
                <button
                  key={targetType}
                  type="button"
                  onClick={() => handleTargetChange(targetType)}
                  disabled={isSubmitting}
                  className={`flex-1 px-3 py-2 text-sm font-medium rounded-md border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    isSelected
                      ? 'bg-blue-50 border-blue-200 text-blue-700'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                  title={config.tooltip}
                  aria-describedby={`tooltip-${targetType}`}
                >
                  {config.label}
                </button>
              );
            })}
          </div>

          {/* Tooltips */}
          <div className="mt-2 text-xs text-gray-500">
            {(['main', 'counter', 'neutral'] as const).map((targetType) => {
              const config = getTargetConfig(targetType);
              return (
                <div
                  key={targetType}
                  id={`tooltip-${targetType}`}
                  className={`${target === targetType ? 'block' : 'hidden'}`}
                >
                  {config.tooltip}
                </div>
              );
            })}
          </div>
        </div>

        <Button
          type="submit"
          disabled={!isValid || isSubmitting}
          className="w-full"
          onClick={() => {
            // Analytics: principles_revision_submitted
            console.log('principles_revision_submitted', {
              principleId: 'current',
              target,
              length: charCount
            });
          }}
        >
          {isSubmitting ? principlesCopy.loading : currentTargetConfig.cta}
        </Button>
      </form>
    </Card>
  );
}
