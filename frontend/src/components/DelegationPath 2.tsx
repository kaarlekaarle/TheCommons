import React from 'react';
import { ArrowRight, User, Shield } from 'lucide-react';
import type { Poll, DelegationSummary } from '../types';
import { flags } from '../config/flags';

interface DelegationPathProps {
  poll: Poll;
  delegationSummary: DelegationSummary | null;
  currentUserId?: string;
}

export const DelegationPath: React.FC<DelegationPathProps> = ({
  poll,
  delegationSummary,
  currentUserId
}) => {
  if (!flags.labelsEnabled || !delegationSummary || !currentUserId) {
    return null;
  }

  // Calculate the effective delegation path
  const calculatePath = () => {
    const path = [];
    
    // Check for direct vote first
    if (poll.your_vote_status?.status === 'voted') {
      return [{ type: 'direct', label: 'You decide directly' }];
    }
    
    // Check for label-specific delegation
    if (poll.labels && poll.labels.length > 0) {
      for (const label of poll.labels) {
        const labelDelegation = delegationSummary.per_label.find(
          d => d.label.slug === label.slug
        );
        if (labelDelegation) {
          path.push({
            type: 'label',
            label: label.name,
            delegate: labelDelegation.delegate.username
          });
          return path;
        }
      }
    }
    
    // Check for global delegation
    if (delegationSummary.global_delegate?.has_delegate) {
      path.push({
        type: 'global',
        delegate: delegationSummary.global_delegate.delegate_username || 'Unknown'
      });
      return path;
    }
    
    // No delegation found
    return [{ type: 'direct', label: 'You decide directly' }];
  };

  const path = calculatePath();

  if (path.length === 1 && path[0].type === 'direct') {
    return (
      <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
        <div className="flex items-center gap-3">
          <Shield className="w-5 h-5 text-blue-300 flex-shrink-0" />
          <div>
            <h3 className="text-blue-200 font-medium text-sm mb-1">How your vote flows</h3>
            <p className="text-blue-300 text-sm">You decide directly on this proposal</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
      <div className="flex items-center gap-3 mb-3">
        <Shield className="w-5 h-5 text-blue-300 flex-shrink-0" />
        <h3 className="text-blue-200 font-medium text-sm">How your vote flows</h3>
      </div>
      
      <div className="flex items-center gap-2 text-sm">
        <div className="flex items-center gap-1">
          <User className="w-4 h-4 text-blue-300" />
          <span className="text-blue-200">You</span>
        </div>
        
        {path.map((step, index) => (
          <React.Fragment key={index}>
            <ArrowRight className="w-4 h-4 text-blue-400" />
            <div className="flex items-center gap-1">
              {step.type === 'label' && (
                <>
                  <span className="px-2 py-1 bg-blue-500/20 text-blue-200 rounded text-xs">
                    {step.label}
                  </span>
                  <span className="text-blue-300">→</span>
                </>
              )}
              <User className="w-4 h-4 text-blue-300" />
              <span className="text-blue-200">
                {step.type === 'label' ? step.delegate : step.delegate}
              </span>
            </div>
          </React.Fragment>
        ))}
      </div>
      
      <div className="mt-2 text-xs text-blue-300/80">
        {path[0].type === 'label' && (
          <span>Delegated by topic: {path[0].label}</span>
        )}
        {path[0].type === 'global' && (
          <span>Globally delegated</span>
        )}
      </div>
    </div>
  );
};

export default DelegationPath;
