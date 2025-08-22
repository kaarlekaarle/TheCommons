import { useState, useEffect, useRef } from 'react';
import { User, Users, Loader2 } from 'lucide-react';
import { getMyDelegation } from '../../lib/api';
import type { DelegationInfo } from '../../types/delegation';
import { delegationCopy } from '../../i18n/en/delegation';
import Button from '../ui/Button';
import ManageDelegationModal from './ManageDelegationModal';
import { trackDelegationViewed, trackDelegationOpened } from '../../lib/analytics';

interface DelegationStatusProps {
  pollId?: string;
  className?: string;
  compact?: boolean;
  onOpenModal?: () => void;
}

export default function DelegationStatus({
  pollId,
  className = '',
  compact = false,
  onOpenModal
}: DelegationStatusProps) {
  const [delegationInfo, setDelegationInfo] = useState<DelegationInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isManagerOpen, setIsManagerOpen] = useState(false);
  const statusRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchDelegation = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getMyDelegation();
        setDelegationInfo(data);
        trackDelegationViewed();
      } catch (err: unknown) {
        const error = err as { message: string };
        setError(error.message || delegationCopy.error_loading);
      } finally {
        setLoading(false);
      }
    };

    fetchDelegation();
  }, [pollId]);

  const formatChain = (chain: Array<{ user_id: string; user_name?: string }>) => {
    if (chain.length === 0) return '';

    const chainParts = chain.map(link => link.user_name || link.user_id.slice(0, 8));
    return chainParts.join(' → ');
  };

  const formatDelegationDate = (dateString?: string) => {
    if (!dateString) return '';

    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return '';
    }
  };

  const handleOpenModal = () => {
    trackDelegationOpened();
    if (onOpenModal) {
      onOpenModal();
    } else {
      setIsManagerOpen(true);
    }
  };

  const renderCompactStatus = () => {
    if (loading) {
      return (
        <div className="flex items-center gap-1.5 text-xs text-muted">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span className="truncate">{delegationCopy.compact_loading}</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center gap-1.5 text-xs text-red-400">
          <span className="truncate">{error}</span>
        </div>
      );
    }

    if (!delegationInfo) {
      return (
        <div className="flex items-center gap-1.5 text-xs text-muted">
          <User className="w-3 h-3" />
          <span className="truncate">{delegationCopy.compact_no_delegation}</span>
        </div>
      );
    }

    // Check for poll-specific delegation first
    if (pollId && delegationInfo.poll && delegationInfo.poll.active) {
      const { poll } = delegationInfo;
      const delegateName = poll.to_user_name || poll.to_user_id.slice(0, 8);
      const depth = poll.chain?.length || 0;
      const delegationDate = formatDelegationDate(delegationInfo.created_at);

      return (
        <div className="flex items-center gap-1.5 text-xs">
          <Users className="w-3 h-3 text-blue-400 flex-shrink-0" />
          <span className="truncate" title={delegationCopy.delegates_poll.replace('{name}', delegateName)}>
            {depth > 0
              ? delegationCopy.compact_delegating_chain
                  .replace('{name}', delegateName)
                  .replace('{depth}', depth.toString())
              : delegationCopy.compact_delegating.replace('{name}', delegateName)
            }
            {delegationDate && ` since ${delegationDate}`}
          </span>
        </div>
      );
    }

    // Check for global delegation
    if (delegationInfo.global && delegationInfo.global.active) {
      const { global } = delegationInfo;
      const delegateName = global.to_user_name || global.to_user_id.slice(0, 8);
      const depth = global.chain?.length || 0;
      const delegationDate = formatDelegationDate(delegationInfo.created_at);

      return (
        <div className="flex items-center gap-1.5 text-xs">
          <Users className="w-3 h-3 text-blue-400 flex-shrink-0" />
          <span className="truncate" title={delegationCopy.delegates_global.replace('{name}', delegateName)}>
            {depth > 0
              ? delegationCopy.compact_delegating_chain
                  .replace('{name}', delegateName)
                  .replace('{depth}', depth.toString())
              : delegationCopy.compact_delegating.replace('{name}', delegateName)
            }
            {delegationDate && ` since ${delegationDate}`}
          </span>
        </div>
      );
    }

    // No delegation
    return (
      <div className="flex items-center gap-1.5 text-xs text-muted">
        <User className="w-3 h-3" />
        <span className="truncate">{delegationCopy.compact_no_delegation}</span>
      </div>
    );
  };

  const renderDelegationStatus = () => {
    if (loading) {
      return (
        <div className="flex items-center gap-2 text-sm text-muted">
          <Loader2 className="w-3 h-3 animate-spin" />
          {delegationCopy.loading}
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center gap-2 text-sm text-red-400">
          <span>{error}</span>
        </div>
      );
    }

    if (!delegationInfo) {
      return (
        <div className="flex items-center gap-2 text-sm text-muted">
          <User className="w-3 h-3" />
          {delegationCopy.votes_self}
        </div>
      );
    }

    // Check for poll-specific delegation first
    if (pollId && delegationInfo.poll && delegationInfo.poll.active) {
      const { poll } = delegationInfo;
      const delegateName = poll.to_user_name || poll.to_user_id.slice(0, 8);
      const chain = formatChain(poll.chain || []);
      const delegationDate = formatDelegationDate(delegationInfo.created_at);

      return (
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm">
            <Users className="w-3 h-3 text-blue-400" />
            <span>{delegationCopy.delegates_poll.replace('{name}', delegateName)}</span>
          </div>
          {chain && (
            <div className="text-xs text-muted">
              {delegationCopy.chain_label.replace('{chain}', chain)} (depth {poll.chain?.length || 0})
            </div>
          )}
          {delegationDate && (
            <div className="text-xs text-muted">
              Since {delegationDate}
            </div>
          )}
        </div>
      );
    }

    // Check for global delegation
    if (delegationInfo.global && delegationInfo.global.active) {
      const { global } = delegationInfo;
      const delegateName = global.to_user_name || global.to_user_id.slice(0, 8);
      const chain = formatChain(global.chain || []);
      const delegationDate = formatDelegationDate(delegationInfo.created_at);

      return (
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm">
            <Users className="w-3 h-3 text-blue-400" />
            <span>{delegationCopy.delegates_global.replace('{name}', delegateName)}</span>
          </div>
          {chain && (
            <div className="text-xs text-muted">
              {delegationCopy.chain_label.replace('{chain}', chain)} (depth {global.chain?.length || 0})
            </div>
          )}
          {delegationDate && (
            <div className="text-xs text-muted">
              Since {delegationDate}
            </div>
          )}
        </div>
      );
    }

    // No delegation
    return (
      <div className="flex items-center gap-2 text-sm text-muted">
        <User className="w-3 h-3" />
        {delegationCopy.votes_self}
      </div>
    );
  };

  if (compact) {
    return (
      <>
        <div
          ref={statusRef}
          className={`flex items-center justify-between ${className} cursor-pointer hover:bg-surface/50 rounded px-2 py-1 transition-colors`}
          onClick={handleOpenModal}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleOpenModal();
            }
          }}
          tabIndex={0}
          role="button"
          aria-label="Manage delegation"
          aria-expanded={isManagerOpen}
        >
          <div className="flex-1 min-w-0">
            {renderCompactStatus()}
          </div>
        </div>

        <ManageDelegationModal
          open={isManagerOpen}
          onClose={() => setIsManagerOpen(false)}
          pollId={pollId}
          onDelegationChange={setDelegationInfo}
        />
      </>
    );
  }

  return (
    <>
      <div className={`flex items-center justify-between ${className}`}>
        <div className="flex-1">
          {renderDelegationStatus()}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="text-xs text-muted hover:text-white"
          onClick={handleOpenModal}
        >
          {delegationCopy.manage_link}
        </Button>
      </div>

      <ManageDelegationModal
        open={isManagerOpen}
        onClose={() => setIsManagerOpen(false)}
        pollId={pollId}
        onDelegationChange={setDelegationInfo}
      />
    </>
  );
}
