import React, { useState } from 'react';
import { X, Users, User, Search, Plus, Trash2 } from 'lucide-react';
import type { DelegationInfo } from '../../types/delegation';
import { delegationCopy } from '../../i18n/en/delegation';
import Button from '../ui/Button';

interface DelegationManagerProps {
  isOpen: boolean;
  onClose: () => void;
  delegationInfo: DelegationInfo | null;
  pollId?: string;
}

export default function DelegationManager({ 
  isOpen, 
  onClose, 
  delegationInfo, 
  pollId 
}: DelegationManagerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  if (!isOpen) return null;

  const currentDelegation = pollId 
    ? delegationInfo?.poll 
    : delegationInfo?.global;

  const handleCreateDelegation = async () => {
    // TODO: Implement delegation creation
    console.log('Create delegation for:', searchQuery);
    setIsCreating(true);
    // Simulate API call
    setTimeout(() => {
      setIsCreating(false);
      onClose();
    }, 1000);
  };

  const handleRemoveDelegation = async () => {
    // TODO: Implement delegation removal
    console.log('Remove delegation');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-surface border border-border rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">{delegationCopy.manager_title}</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-muted hover:text-white"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Current Status */}
        <div className="mb-6 p-4 bg-surface/50 border border-border rounded-lg">
          <h3 className="text-sm font-medium text-white mb-2">{delegationCopy.current_status}</h3>
          {currentDelegation && currentDelegation.active ? (
            <div className="flex items-center gap-2 text-sm">
              <Users className="w-4 h-4 text-blue-400" />
              <span>
                {pollId 
                  ? delegationCopy.delegates_poll.replace('{name}', currentDelegation.to_user_name || currentDelegation.to_user_id.slice(0, 8))
                  : delegationCopy.delegates_global.replace('{name}', currentDelegation.to_user_name || currentDelegation.to_user_id.slice(0, 8))
                }
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-muted">
              <User className="w-4 h-4" />
              {delegationCopy.votes_self}
            </div>
          )}
        </div>

        {/* Create New Delegation */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-white">{delegationCopy.create_new}</h3>
          
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted" />
              <input
                type="text"
                placeholder={delegationCopy.search_placeholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-surface border border-border rounded-lg text-white placeholder-muted focus:border-primary focus:outline-none"
              />
            </div>

            {/* TODO: Add user search results here */}
            {searchQuery && (
              <div className="p-3 bg-surface/50 border border-border rounded-lg">
                <p className="text-sm text-muted">
                  {delegationCopy.search_results_placeholder}
                </p>
              </div>
            )}

            <Button
              onClick={handleCreateDelegation}
              disabled={!searchQuery.trim() || isCreating}
              className="w-full"
            >
              {isCreating ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {delegationCopy.creating}
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  {delegationCopy.delegate_to.replace('{name}', searchQuery || 'user')}
                </div>
              )}
            </Button>
          </div>
        </div>

        {/* Remove Current Delegation */}
        {currentDelegation && currentDelegation.active && (
          <div className="mt-6 pt-6 border-t border-border">
            <h3 className="text-sm font-medium text-white mb-3">{delegationCopy.remove_delegation}</h3>
            <Button
              variant="ghost"
              onClick={handleRemoveDelegation}
              className="w-full text-red-400 hover:text-red-300 hover:bg-red-500/10"
            >
              <div className="flex items-center gap-2">
                <Trash2 className="w-4 h-4" />
                Remove Delegation
              </div>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
