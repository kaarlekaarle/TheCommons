import React, { useState, useEffect } from 'react';
import { X, Users, User, BarChart3, Loader2, AlertCircle } from 'lucide-react';
import { getMyChains, getInbound, getHealthSummary } from '../../api/delegationsApi';
import Button from '../ui/Button';

interface TransparencyPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'chains' | 'inbound' | 'health';

export default function TransparencyPanel({
  isOpen,
  onClose
}: TransparencyPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>('chains');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Chains data
  const [chains, setChains] = useState<any>(null);
  
  // Inbound data
  const [delegateeId, setDelegateeId] = useState('');
  const [fieldId, setFieldId] = useState('');
  const [inboundData, setInboundData] = useState<any>(null);
  
  // Health data
  const [healthData, setHealthData] = useState<any>(null);

  // Load data based on active tab
  useEffect(() => {
    if (!isOpen) return;
    
    setError(null);
    setLoading(true);
    
    switch (activeTab) {
      case 'chains':
        loadChains();
        break;
      case 'health':
        loadHealth();
        break;
      default:
        setLoading(false);
    }
  }, [isOpen, activeTab]);

  const loadChains = async () => {
    try {
      const data = await getMyChains();
      setChains(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load delegation chains');
    } finally {
      setLoading(false);
    }
  };

  const loadInbound = async () => {
    if (!delegateeId.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await getInbound(delegateeId, fieldId || undefined);
      setInboundData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load inbound delegations');
    } finally {
      setLoading(false);
    }
  };

  const loadHealth = async () => {
    try {
      const data = await getHealthSummary();
      setHealthData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load health summary');
    } finally {
      setLoading(false);
    }
  };

  const renderChainsTab = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center gap-2 text-danger-fg p-4 bg-danger-bg rounded-lg">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      );
    }

    if (!chains || chains.chains.length === 0) {
      return (
        <div className="text-center text-fg-muted py-8">
          <Users className="w-12 h-12 mx-auto mb-4 text-fg-muted/50" />
          <p>No delegation chains found</p>
          <p className="text-sm">You haven't created any delegations yet.</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <p className="text-sm text-fg-muted">
          Your delegation chains grouped by field:
        </p>
        {chains.chains.map((chain: any, index: number) => (
          <div key={index} className="p-4 bg-surface-muted rounded-lg border">
            <h4 className="font-medium text-fg-strong mb-2">
              Field: {chain.fieldName || chain.fieldId}
            </h4>
            <div className="space-y-2">
              {chain.path.map((link: any, linkIndex: number) => (
                <div key={linkIndex} className="flex items-center gap-2 text-sm">
                  <span className="text-fg-muted">
                    {link.delegatorName || link.delegatorId}
                  </span>
                  <span className="text-fg-muted">→</span>
                  <span className="font-medium">
                    {link.delegateeName || link.delegateeId}
                  </span>
                  <span className="text-xs text-fg-muted">
                    ({link.mode})
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderInboundTab = () => {
    return (
      <div className="space-y-4">
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-fg-strong mb-1">
              Delegatee ID
            </label>
            <input
              type="text"
              value={delegateeId}
              onChange={(e) => setDelegateeId(e.target.value)}
              placeholder="Enter delegatee ID"
              className="w-full px-3 py-2 border border-border rounded-lg bg-surface text-fg-strong"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-fg-strong mb-1">
              Field ID (optional)
            </label>
            <input
              type="text"
              value={fieldId}
              onChange={(e) => setFieldId(e.target.value)}
              placeholder="Enter field ID to filter"
              className="w-full px-3 py-2 border border-border rounded-lg bg-surface text-fg-strong"
            />
          </div>
          <Button
            onClick={loadInbound}
            disabled={!delegateeId.trim() || loading}
            className="w-full"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Load Inbound'}
          </Button>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-danger-fg p-4 bg-danger-bg rounded-lg">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {inboundData && (
          <div className="space-y-4">
            <div className="p-4 bg-surface-muted rounded-lg border">
              <h4 className="font-medium text-fg-strong mb-2">
                {inboundData.delegateeName || inboundData.delegateeId}
              </h4>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-fg-muted">Total inbound:</span>
                  <span className="font-medium ml-2">{inboundData.counts.total}</span>
                </div>
                {Object.keys(inboundData.counts.byField).length > 0 && (
                  <div>
                    <span className="text-fg-muted">By field:</span>
                    <div className="mt-1 space-y-1">
                      {Object.entries(inboundData.counts.byField).map(([fieldId, count]: [string, any]) => (
                        <div key={fieldId} className="ml-4">
                          <span className="text-fg-muted">{fieldId}:</span>
                          <span className="font-medium ml-2">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {inboundData.inbound.length > 0 && (
              <div>
                <h5 className="font-medium text-fg-strong mb-2">Recent delegations:</h5>
                <div className="space-y-2">
                  {inboundData.inbound.slice(0, 10).map((delegation: any, index: number) => (
                    <div key={index} className="p-3 bg-surface-muted rounded-lg border text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">
                          {delegation.delegatorName || delegation.delegatorId}
                        </span>
                        <span className="text-fg-muted text-xs">
                          {delegation.fieldName || delegation.fieldId}
                        </span>
                      </div>
                      <div className="text-xs text-fg-muted mt-1">
                        {new Date(delegation.createdAt).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderHealthTab = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center gap-2 text-danger-fg p-4 bg-danger-bg rounded-lg">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      );
    }

    if (!healthData) {
      return (
        <div className="text-center text-fg-muted py-8">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 text-fg-muted/50" />
          <p>No health data available</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="p-4 bg-surface-muted rounded-lg border">
          <h4 className="font-medium text-fg-strong mb-3">Top Delegatees</h4>
          <div className="space-y-2">
            {healthData.topDelegatees?.map((delegatee: any, index: number) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="font-medium">
                  {delegatee.name || delegatee.id}
                </span>
                <span className="text-fg-muted">
                  {delegatee.percent ? `${(delegatee.percent * 100).toFixed(1)}%` : 'N/A'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {healthData.byField && Object.keys(healthData.byField).length > 0 && (
          <div className="p-4 bg-surface-muted rounded-lg border">
            <h4 className="font-medium text-fg-strong mb-3">By Field</h4>
            <div className="space-y-3">
              {Object.entries(healthData.byField).map(([fieldId, fieldData]: [string, any]) => (
                <div key={fieldId}>
                  <h5 className="font-medium text-fg-strong mb-2">{fieldData.fieldName || fieldId}</h5>
                  <div className="space-y-1">
                    {fieldData.top?.map((delegatee: any, index: number) => (
                      <div key={index} className="flex items-center justify-between text-sm">
                        <span>{delegatee.name || delegatee.id}</span>
                        <span className="text-fg-muted">
                          {delegatee.percent ? `${(delegatee.percent * 100).toFixed(1)}%` : 'N/A'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="absolute right-0 top-0 h-full w-full max-w-2xl bg-surface border-l border-border shadow-xl transform transition-transform duration-300 ease-in-out">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <h2 className="text-xl font-semibold text-fg-strong">Transparency Panel</h2>
            <button
              onClick={onClose}
              className="p-2 text-fg-muted hover:text-fg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-border">
            <button
              onClick={() => setActiveTab('chains')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'chains'
                  ? 'text-primary-600 border-b-2 border-primary-600'
                  : 'text-fg-muted hover:text-fg'
              }`}
            >
              My Chains
            </button>
            <button
              onClick={() => setActiveTab('inbound')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'inbound'
                  ? 'text-primary-600 border-b-2 border-primary-600'
                  : 'text-fg-muted hover:text-fg'
              }`}
            >
              Who Delegates to X
            </button>
            <button
              onClick={() => setActiveTab('health')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'health'
                  ? 'text-primary-600 border-b-2 border-primary-600'
                  : 'text-fg-muted hover:text-fg'
              }`}
            >
              Health
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'chains' && renderChainsTab()}
            {activeTab === 'inbound' && renderInboundTab()}
            {activeTab === 'health' && renderHealthTab()}
          </div>
        </div>
      </div>
    </div>
  );
}
