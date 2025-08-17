import React, { useState, useEffect } from 'react';
import { User, Hash, Calendar, X } from 'lucide-react';
import { useToast } from '../ui/useToast';
import { createDelegation, trackComposerOpen, trackDelegationCreated, searchPeople, searchFields } from '../../api/delegationsApi';
import type { PersonSearchResult, FieldSearchResult, CreateDelegationInput, DelegationWarnings } from '../../api/delegationsApi';
import Button from '../ui/Button';

interface InlineCommonsFormProps {
  onSubmitted?: () => void;
  defaults?: { fieldId?: string; personId?: string; expiryDate?: string | null };
  onCollapse?: () => void;
}

export default function InlineCommonsForm({
  onSubmitted,
  defaults,
  onCollapse
}: InlineCommonsFormProps) {
  const [selectedField, setSelectedField] = useState<FieldSearchResult | null>(null);
  const [selectedPerson, setSelectedPerson] = useState<PersonSearchResult | null>(null);
  const [fieldQuery, setFieldQuery] = useState('');
  const [personQuery, setPersonQuery] = useState('');
  const [fields, setFields] = useState<FieldSearchResult[]>([]);
  const [people, setPeople] = useState<PersonSearchResult[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [expiry, setExpiry] = useState(defaults?.expiryDate || '');
  const [warnings, setWarnings] = useState<DelegationWarnings>({});
  const { success, error: showError } = useToast();

  // Emit telemetry on mount and focus first input
  useEffect(() => {
    trackComposerOpen('commons');
    // Focus the field search input when form opens
    const fieldInput = document.querySelector('input[placeholder="Search for a field..."]') as HTMLInputElement;
    if (fieldInput) {
      fieldInput.focus();
    }
  }, []);

  // Search fields
  useEffect(() => {
    let cancelled = false;

    async function searchFieldsData() {
      if (!fieldQuery.trim()) {
        setFields([]);
        return;
      }

      try {
        const results = await searchFields(fieldQuery);
        if (!cancelled) {
          setFields(results);
        }
      } catch (err) {
        console.error('Failed to search fields:', err);
      }
    }

    const timeoutId = setTimeout(searchFieldsData, 250);
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [fieldQuery]);

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
    
    if (!selectedField) {
      showError('Please select a field to delegate');
      return;
    }

    if (!selectedPerson) {
      showError('Please select a person to delegate to');
      return;
    }

    setSubmitting(true);
    setWarnings({});

    try {
      const input: CreateDelegationInput = {
        mode: 'commons',
        delegatee_id: selectedPerson.id,
        field_id: selectedField.id,
        expiry: expiry ? new Date(expiry).toISOString() : undefined,
      };

      const response = await createDelegation(input);
      
      if (response.warnings) {
        setWarnings(response.warnings);
      }

      success(`Successfully delegated ${selectedField.label} to ${selectedPerson.displayName}`);
      trackDelegationCreated('commons');
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
    <div className="border-t border-border pt-4 mt-4" role="region" aria-labelledby="commons-title">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-medium text-fg-strong">Create Commons Delegation</h4>
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
                  <strong>High concentration:</strong> ~{(warnings.concentration.percent * 100).toFixed(1)}% of delegations in this field go to this person.
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

        {/* Field Selection */}
        <div>
          <label className="block text-sm font-medium text-fg-strong mb-2">
            Field
          </label>
          <div className="relative">
            <input
              type="text"
              value={fieldQuery}
              onChange={(e) => setFieldQuery(e.target.value)}
              placeholder="Search for a field..."
              className="w-full px-3 py-2 border border-border rounded-lg bg-surface text-fg placeholder-placeholder focus:outline-none focus:ring-2 focus:ring-primary-600"
            />
            <Hash className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-fg-muted" />
          </div>

          {/* Fields results */}
          {fields.length > 0 && (
            <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
              {fields.map((field) => (
                <button
                  key={field.id}
                  type="button"
                  onClick={() => {
                    setSelectedField(field);
                    setFieldQuery('');
                    setFields([]);
                  }}
                  className="w-full p-2 text-left bg-surface-muted border border-border rounded-lg hover:bg-surface-muted/80 transition-colors"
                >
                  <div className="font-medium text-fg-strong">{field.label}</div>
                  {field.description && (
                    <div className="text-sm text-fg-muted">{field.description}</div>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* Selected field */}
          {selectedField && (
            <div className="mt-2 p-3 bg-primary-50 border border-primary-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-primary-900">{selectedField.label}</div>
                  {selectedField.description && (
                    <div className="text-sm text-primary-700">{selectedField.description}</div>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedField(null)}
                  className="text-primary-600 hover:text-primary-800"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

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

        {/* Optional Expiry */}
        <div>
          <label className="block text-sm font-medium text-fg-strong mb-2">
            Expiry (Optional)
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
            {expiry ? `Expires: ${formatExpiryDate(expiry)}` : 'No expiry set'} • Revocable anytime
          </p>
        </div>

        {/* Preview */}
        {selectedField && selectedPerson && (
          <div className="p-3 bg-info-bg border border-info-fg/20 rounded-lg">
            <p className="text-sm text-info-fg">
              <strong>Preview:</strong> You will delegate: You → {selectedPerson.displayName}, scope: {selectedField.label}, expiry: {expiry ? formatExpiryDate(expiry) : 'none'}
            </p>
          </div>
        )}

        {/* Submit Button */}
        <Button
          type="submit"
          disabled={!selectedField || !selectedPerson || submitting}
          className="w-full"
        >
          {submitting ? 'Creating...' : `Delegate for ${selectedField?.label || 'this field'}`}
        </Button>
      </form>
    </div>
  );
}
