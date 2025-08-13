import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, Search, Users, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { searchUsers, createDelegation, removeDelegation, getMyDelegation, type UserSearchResult } from '../../lib/api';
import type { DelegationInfo } from '../../types/delegation';
import { delegationCopy } from '../../i18n/en/delegation';
import Button from '../ui/Button';
import { trackDelegationCreated, trackDelegationRevoked } from '../../lib/analytics';

interface ManageDelegationModalProps {
  open: boolean;
  onClose: () => void;
  pollId?: string;
  onDelegationChange?: (delegationInfo: DelegationInfo | null) => void;
}

type Mode = 'create' | 'revoke';
type Scope = 'poll' | 'global';

export default function ManageDelegationModal({ 
  open, 
  onClose, 
  pollId,
  onDelegationChange 
}: ManageDelegationModalProps) {
  const [mode, setMode] = useState<Mode>('create');
  const [scope, setScope] = useState<Scope>(pollId ? 'poll' : 'global');
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserSearchResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [currentDelegation, setCurrentDelegation] = useState<DelegationInfo | null>(null);
  const [chainExpanded, setChainExpanded] = useState(false);
  
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const modalRef = useRef<HTMLDivElement>(null);

  // Debounced search
  const debouncedSearch = useCallback((searchQuery: string) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setSearching(false);
      return;
    }

    setSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const results = await searchUsers(searchQuery);
        setSearchResults(results);
      } catch (err) {
        console.error('Search failed:', err);
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
  }, []);

  // Handle query changes
  useEffect(() => {
    debouncedSearch(query);
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [query, debouncedSearch]);

  // Load current delegation on mount
  useEffect(() => {
    if (open) {
      loadCurrentDelegation();
    }
  }, [open]);

  // Determine mode and scope based on current delegation
  useEffect(() => {
    if (currentDelegation) {
      if (pollId && currentDelegation.poll?.active) {
        setMode('revoke');
        setScope('poll');
      } else if (currentDelegation.global?.active) {
        setMode('revoke');
        setScope('global');
      } else {
        setMode('create');
        setScope(pollId ? 'poll' : 'global');
      }
    } else {
      setMode('create');
      setScope(pollId ? 'poll' : 'global');
    }
  }, [currentDelegation, pollId]);

  const loadCurrentDelegation = async () => {
    try {
      const delegation = await getMyDelegation();
      setCurrentDelegation(delegation);
    } catch (err) {
      console.error('Failed to load delegation:', err);
    }
  };

  const handleCreateDelegation = async () => {
    if (!selectedUser) return;

    setSubmitting(true);
    setError(null);

    try {
      // Optimistic update
      const optimisticDelegation: DelegationInfo = {
        ...currentDelegation,
        [scope]: {
          to_user_id: selectedUser.id,
          to_user_name: selectedUser.name,
          active: true,
          chain: [{ user_id: 'current-user', user_name: 'You' }]
        }
      };
      
      if (onDelegationChange) {
        onDelegationChange(optimisticDelegation);
      }

      await createDelegation({
        to_user_id: selectedUser.id,
        scope,
        poll_id: scope === 'poll' ? pollId : undefined
      });

      trackDelegationCreated(scope);

      // Refresh delegation to get full chain
      await loadCurrentDelegation();
      onClose();
    } catch (err: unknown) {
      const error = err as { message?: string };
      setError(error.message || delegationCopy.error_generic);
      // Revert optimistic update
      if (onDelegationChange) {
        onDelegationChange(currentDelegation);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevokeDelegation = async () => {
    setSubmitting(true);
    setError(null);

    try {
      // Optimistic update
      const optimisticDelegation: DelegationInfo = {
        ...currentDelegation,
        [scope]: undefined
      };
      
      if (onDelegationChange) {
        onDelegationChange(optimisticDelegation);
      }

      await removeDelegation({
        scope,
        poll_id: scope === 'poll' ? pollId : undefined
      });

      trackDelegationRevoked(scope);

      // Refresh delegation
      await loadCurrentDelegation();
      onClose();
    } catch (err: unknown) {
      const error = err as { message?: string };
      setError(error.message || delegationCopy.error_generic);
      // Revert optimistic update
      if (onDelegationChange) {
        onDelegationChange(currentDelegation);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'Enter' && mode === 'create' && selectedUser && !submitting) {
      handleCreateDelegation();
    }
  };

  const getCurrentDelegationInfo = () => {
    if (scope === 'poll' && currentDelegation?.poll?.active) {
      return currentDelegation.poll;
    } else if (scope === 'global' && currentDelegation?.global?.active) {
      return currentDelegation.global;
    }
    return null;
  };

  const scopeLabel = scope === 'poll' ? 'this poll' : 'all polls';
  const currentDelegationInfo = getCurrentDelegationInfo();

  if (!open) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div 
        ref={modalRef}
        className="bg-surface border border-border rounded-lg p-6 w-full max-w-md mx-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delegation-modal-title"
        onKeyDown={handleKeyDown}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 id="delegation-modal-title" className="text-xl font-semibold text-white">
            {delegationCopy.manage_title}
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-muted hover:text-white"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Scope Selection */}
        <div className="mb-6">
          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="scope"
                value="poll"
                checked={scope === 'poll'}
                onChange={() => setScope('poll')}
                disabled={!pollId}
                className="text-primary"
              />
              <span className="text-sm text-white">
                {delegationCopy.scope_poll}
              </span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="scope"
                value="global"
                checked={scope === 'global'}
                onChange={() => setScope('global')}
                className="text-primary"
              />
              <span className="text-sm text-white">
                {delegationCopy.scope_global}
              </span>
            </label>
          </div>
        </div>

        {mode === 'create' ? (
          /* Create Mode */
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted" />
              <input
                type="text"
                placeholder={delegationCopy.search_placeholder_new}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-surface border border-border rounded-lg text-white placeholder-muted focus:border-primary focus:outline-none"
                autoFocus
              />
            </div>

            {/* Search Results */}
            {searching && (
              <div className="flex items-center gap-2 text-sm text-muted">
                <Loader2 className="w-4 h-4 animate-spin" />
                Searching...
              </div>
            )}

            {!searching && query && searchResults.length === 0 && (
              <div className="text-sm text-muted">
                {delegationCopy.no_results}
              </div>
            )}

            {searchResults.length > 0 && (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {searchResults.map((searchUser) => {
                  const isCurrentUser = false; // TODO: Implement current user check
                  const isSelected = selectedUser?.id === searchUser.id;
                  
                  return (
                    <button
                      key={searchUser.id}
                      onClick={() => !isCurrentUser && setSelectedUser(searchUser)}
                      disabled={isCurrentUser}
                      className={`w-full p-3 rounded-lg border text-left transition-colors ${
                        isSelected 
                          ? 'border-primary bg-primary/10' 
                          : 'border-border hover:border-primary/50'
                      } ${isCurrentUser ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                          {searchUser.avatar_url ? (
                            <img src={searchUser.avatar_url} alt="" className="w-8 h-8 rounded-full" />
                          ) : (
                            <span className="text-sm font-medium text-primary">
                              {searchUser.name.charAt(0).toUpperCase()}
                            </span>
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="text-sm font-medium text-white">{searchUser.name}</div>
                          {isCurrentUser && (
                            <div className="text-xs text-muted">
                              {delegationCopy.self_delegation_hint}
                            </div>
                          )}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            <Button
              onClick={handleCreateDelegation}
              disabled={!selectedUser || submitting}
              className="w-full"
            >
              {submitting ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {delegationCopy.delegating}
                </div>
              ) : (
                delegationCopy.delegate_cta
              )}
            </Button>
          </div>
        ) : (
          /* Revoke Mode */
          <div className="space-y-4">
            <div className="p-4 bg-surface/50 border border-border rounded-lg">
              <div className="flex items-center gap-2 text-sm">
                <Users className="w-4 h-4 text-blue-400" />
                <span>
                  You currently delegate {scopeLabel} to{' '}
                  {currentDelegationInfo?.to_user_name || currentDelegationInfo?.to_user_id?.slice(0, 8)}
                </span>
              </div>
              
              {/* Chain Display */}
              {currentDelegationInfo?.chain && currentDelegationInfo.chain.length > 0 && (
                <div className="mt-3">
                  <button
                    onClick={() => setChainExpanded(!chainExpanded)}
                    className="flex items-center gap-2 text-xs text-muted hover:text-white transition-colors"
                  >
                    {chainExpanded ? (
                      <ChevronUp className="w-3 h-3" />
                    ) : (
                      <ChevronDown className="w-3 h-3" />
                    )}
                    <span>Chain ({currentDelegationInfo.chain.length})</span>
                  </button>
                  
                  {chainExpanded && (
                    <div className="mt-2 space-y-1">
                      {currentDelegationInfo.chain.map((link, index) => (
                        <div key={index} className="flex items-center gap-2 text-xs text-muted">
                          <div className="w-2 h-2 rounded-full bg-muted" />
                          <span>{link.user_name || link.user_id.slice(0, 8)}</span>
                          {index < currentDelegationInfo.chain.length - 1 && (
                            <ChevronDown className="w-2 h-2" />
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <Button
              variant="ghost"
              onClick={handleRevokeDelegation}
              disabled={submitting}
              className="w-full text-red-400 hover:text-red-300 hover:bg-red-500/10"
            >
              {submitting ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {delegationCopy.revoking}
                </div>
              ) : (
                delegationCopy.revoke_cta
              )}
            </Button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Helper Text */}
        <div className="mt-6 pt-4 border-t border-border">
          <p className="text-xs text-muted leading-relaxed">
            {delegationCopy.helper_text}
          </p>
        </div>
      </div>
    </div>
  );
}
