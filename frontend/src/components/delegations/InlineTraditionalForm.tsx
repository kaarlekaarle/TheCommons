import React, { useState, useEffect } from 'react';
import { User, Calendar, X } from 'lucide-react';
import { useToast } from '../ui/useToast';
import { createDelegation, trackComposerOpen, trackDelegationCreated, searchPeople } from '../../api/delegationsApi';
import type { PersonSearchResult, CreateDelegationInput, DelegationWarnings } from '../../api/delegationsApi';
import Button from '../ui/Button';

interface InlineTraditionalFormProps {
  onSubmitted?: () => void;
  defaults?: { personId?: string; termDate?: string };
  onCollapse?: () => void;
}

export default function InlineTraditionalForm({
  onSubmitted,
  defaults,
  onCollapse
}: InlineTraditionalFormProps) {
  const [selectedPerson, setSelectedPerson] = useState<PersonSearchResult | null>(null);
  const [personQuery, setPersonQuery] = useState('');
  const [people, setPeople] = useState<PersonSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [expiry, setExpiry] = useState(defaults?.termDate || '');
  const [warnings, setWarnings] = useState<DelegationWarnings>({});
  const { success, error: showError } = useToast();

  // Calculate default expiry (4 years from now)
  const defaultExpiry = new Date();
  defaultExpiry.setFullYear(defaultExpiry.getFullYear() + 4);

  // Emit telemetry on mount and focus first input
  useEffect(() => {
    trackComposerOpen('traditional');
    // Focus the person search input when form opens
    const personInput = document.querySelector('input[placeholder="Search for a person..."]') as HTMLInputElement;
    if (personInput) {
      personInput.focus();
    }
  }, []);

  // Set default expiry if not provided
  useEffect(() => {
    if (!expiry) {
      setExpiry(defaultExpiry.toISOString().split('T')[0]);
    }
  }, [expiry, defaultExpiry]);

  // Search people
  useEffect(() => {
    let cancelled = false;

    async function searchPeopleData() {
      if (!personQuery.trim()) {
        setPeople([]);
        return;
      }

      try {
        const results = await searchPeople(personQuery);
        if (!cancelled) {
          setPeople(results);
        }
      } catch (err) {
        console.error('Failed to search people:', err);
      }
    }

    const timeoutId = setTimeout(searchPeopleData, 250);
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [personQuery]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedPerson) {
      showError('Please select a person to delegate to');
      return;
    }

    setSubmitting(true);
    setWarnings({});

    try {
      const input: CreateDelegationInput = {
        mode: 'traditional',
        delegatee_id: selectedPerson.id,
        expiry: expiry ? new Date(expiry).toISOString() : undefined,
      };

      const response = await createDelegation(input);
      
      if (response.warnings) {
        setWarnings(response.warnings);
      }

      success(`Successfully delegated all power to ${selectedPerson.displayName}`);
      trackDelegationCreated('traditional');
      onSubmitted?.();
    } catch (err: unknown) {
      const error = err as { message?: string };
      showError(error.message || 'Failed to create delegation');
    } finally {
      setSubmitting(false);
    }
  };

  const formatExpiryDate = (dateString: string) => {
    if (!dateString) return 'No expiry';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="border-t border-border pt-4 mt-4 bg-surface-muted/30 rounded-lg p-4" role="region" aria-labelledby="traditional-title">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-medium text-fg-strong">Create Traditional Delegation</h4>
        <button
          onClick={onCollapse}
          className="p-1 text-fg-muted hover:text-fg transition-colors"
          aria-label="Collapse form"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Constitutional Warnings */}
        {(warnings.concentration || warnings.superDelegateRisk) && (
          <div className="space-y-2">
            {warnings.concentration && (
              <div className="p-3 bg-warn-bg border border-warn-fg/20 rounded-lg">
                <p className="text-sm text-warn-fg">
                  <strong>High concentration:</strong> ~{(warnings.concentration.percent * 100).toFixed(1)}% of delegations go to this person.
                </p>
              </div>
            )}
            {warnings.superDelegateRisk && (
              <div className="p-3 bg-warn-bg border border-warn-fg/20 rounded-lg">
                <p className="text-sm text-warn-fg">
                  <strong>Super-delegate:</strong> This could create a 'super-delegate' pattern: {warnings.superDelegateRisk.reason}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Person Selection */}
        <div>
          <label className="block text-sm font-medium text-fg-strong mb-2">
            Person
          </label>
          <div className="relative">
            <input
              type="text"
              value={personQuery}
              onChange={(e) => setPersonQuery(e.target.value)}
              placeholder="Search for a person..."
              className="w-full px-3 py-2 border border-border rounded-lg bg-surface text-fg placeholder-placeholder focus:outline-none focus:ring-2 focus:ring-primary-600"
            />
            <User className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-fg-muted" />
          </div>

          {/* People results */}
          {people.length > 0 && (
            <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
              {people.map((person) => (
                <button
                  key={person.id}
                  type="button"
                  onClick={() => {
                    setSelectedPerson(person);
                    setPersonQuery('');
                    setPeople([]);
                  }}
                  className="w-full p-2 text-left bg-surface-muted border border-border rounded-lg hover:bg-surface-muted/80 transition-colors"
                >
                  <div className="font-medium text-fg-strong">{person.displayName}</div>
                  {person.bio && (
                    <div className="text-sm text-fg-muted">{person.bio}</div>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Selected person */}
          {selectedPerson && (
            <div className="mt-2 p-3 bg-primary-50 border border-primary-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-primary-900">{selectedPerson.displayName}</div>
                  {selectedPerson.bio && (
                    <div className="text-sm text-primary-700">{selectedPerson.bio}</div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedPerson(null)}
                  className="text-primary-600 hover:text-primary-800"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Term Date */}
        <div>
          <label className="block text-sm font-medium text-fg-strong mb-2">
            Term
          </label>
          <div className="relative">
            <input
              type="date"
              value={expiry}
              onChange={(e) => setExpiry(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-surface text-fg focus:outline-none focus:ring-2 focus:ring-primary-600"
            />
            <Calendar className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-fg-muted" />
          </div>
          <p className="mt-1 text-sm text-fg-muted">
            Expires: {formatExpiryDate(expiry)} • Revocable anytime
          </p>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          disabled={!selectedPerson || submitting}
          className="w-full"
        >
          {submitting ? 'Creating...' : `Delegate all to ${selectedPerson?.displayName || 'Person'}`}
        </Button>
      </form>
    </div>
  );
}
