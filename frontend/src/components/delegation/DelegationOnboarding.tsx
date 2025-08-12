import React, { useEffect, useRef, useState } from 'react';
import { X, ExternalLink } from 'lucide-react';
import { delegationCopy } from '../../i18n/en/delegation';
import Button from '../ui/Button';
import { trackOnboardingSeen } from '../../lib/analytics';

interface DelegationOnboardingProps {
  anchorRef: React.RefObject<HTMLElement | null>;
  onClose: () => void;
  onLearnMore: () => void;
}

export default function DelegationOnboarding({ 
  anchorRef, 
  onClose, 
  onLearnMore 
}: DelegationOnboardingProps) {
  const [position, setPosition] = useState<'top' | 'bottom'>('bottom');
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updatePosition = () => {
      if (!anchorRef.current || !tooltipRef.current) return;
      
      const anchorRect = anchorRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      
      // Check if there's enough space below, otherwise position above
      const spaceBelow = viewportHeight - anchorRect.bottom;
      const spaceAbove = anchorRect.top;
      
      if (spaceBelow >= tooltipRect.height || spaceBelow > spaceAbove) {
        setPosition('bottom');
      } else {
        setPosition('top');
      }
    };

    updatePosition();
    window.addEventListener('resize', updatePosition);
    return () => window.removeEventListener('resize', updatePosition);
  }, [anchorRef]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleGotIt = () => {
    // Mark onboarding as seen permanently (stored in localStorage)
    // This prevents the tooltip from showing again on this device
    localStorage.setItem('commons.delegation.onboarded', 'true');
    trackOnboardingSeen();
    onClose();
  };

  const handleLearnMore = () => {
    trackOnboardingSeen();
    onLearnMore();
  };

  if (!anchorRef.current) return null;

  const anchorRect = anchorRef.current.getBoundingClientRect();
  
  const tooltipStyles = {
    position: 'fixed' as const,
    left: Math.max(8, Math.min(anchorRect.left, window.innerWidth - 320 - 8)),
    [position === 'bottom' ? 'top' : 'bottom']: position === 'bottom' 
      ? anchorRect.bottom + 8 
      : anchorRect.top - 8,
    zIndex: 50,
  };

  return (
    <div
      ref={tooltipRef}
      style={tooltipStyles}
      className="w-80 bg-surface border border-border rounded-lg shadow-lg p-4"
      role="dialog"
      aria-labelledby="onboarding-title"
      aria-describedby="onboarding-body"
    >
      {/* Arrow */}
      <div 
        className={`absolute w-3 h-3 bg-surface border-l border-t border-border transform rotate-45 ${
          position === 'bottom' 
            ? '-top-1.5 left-4' 
            : '-bottom-1.5 left-4'
        }`}
      />
      
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <h3 
          id="onboarding-title" 
          className="text-sm font-semibold text-white pr-4"
        >
          {delegationCopy.onboarding_title}
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="text-muted hover:text-white -mt-1 -mr-1"
          aria-label="Close tooltip"
        >
          <X className="w-3 h-3" />
        </Button>
      </div>
      
      {/* Body */}
      <p 
        id="onboarding-body" 
        className="text-sm text-muted mb-4 leading-relaxed"
      >
        {delegationCopy.onboarding_body}
      </p>
      
      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleGotIt}
          className="text-xs"
        >
          {delegationCopy.onboarding_got_it}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleLearnMore}
          className="text-xs"
        >
          <ExternalLink className="w-3 h-3 mr-1" />
          {delegationCopy.onboarding_learn_more}
        </Button>
      </div>
    </div>
  );
}
