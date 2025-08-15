import React, { useState, useEffect, useRef } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import TextArea from '../ui/TextArea';
import { principlesDocCopy } from '../../copy/principlesDoc';

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

  const getTargetLabel = (targetType: 'main' | 'counter' | 'neutral') => {
    switch (targetType) {
      case 'main': return principlesDocCopy.targetMain;
      case 'counter': return principlesDocCopy.targetCounter;
      case 'neutral': return principlesDocCopy.targetNeutral;
    }
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {principlesDocCopy.composerTitle}
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <TextArea
            ref={textareaRef}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder={placeholder || principlesDocCopy.composerPlaceholder}
            className="min-h-[120px] resize-none w-full"
            disabled={isSubmitting}
            aria-describedby="char-count"
          />
          <div
            id="char-count"
            className={`text-sm mt-1 ${
              charCount > 1000 ? 'text-red-600' :
              charCount >= 240 ? 'text-gray-600' : 'text-gray-400'
            }`}
          >
            {charCount}/1000 • {principlesDocCopy.minMax}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {principlesDocCopy.composerTargetLabel}
          </label>
          <div className="flex gap-2">
            {(['main', 'counter', 'neutral'] as const).map((targetType) => (
              <Button
                key={targetType}
                type="button"
                variant={target === targetType ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleTargetChange(targetType)}
                disabled={isSubmitting}
                className="flex-1"
              >
                {getTargetLabel(targetType)}
              </Button>
            ))}
          </div>
        </div>

        <Button
          type="submit"
          disabled={!isValid || isSubmitting}
          className="w-full"
        >
          {isSubmitting ? principlesDocCopy.loading : principlesDocCopy.post}
        </Button>
      </form>
    </Card>
  );
}
