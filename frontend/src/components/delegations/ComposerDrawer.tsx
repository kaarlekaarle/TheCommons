// DEPRECATED: replaced by InlineTraditionalForm/InlineCommonsForm rendered on DelegationsPage.
// Kept temporarily for potential reuse. Do not import this component in DelegationsPage.

import { useState, useEffect } from 'react';
import { X, Calendar, User, Hash, AlertTriangle } from 'lucide-react';
import { useToast } from '../ui/useToast';
import { createDelegation, trackDelegationCreated } from '../../api/delegationsApi';
import { searchPeople, searchFields } from '../../api/delegationsApi';
import type { PersonSearchResult, FieldSearchResult, CreateDelegationInput, DelegationWarnings } from '../../api/delegationsApi';
import Button from '../ui/Button';

interface ComposerDrawerProps {
  open: boolean;
  onClose: () => void;
  defaultPerson?: PersonSearchResult;
  defaultField?: FieldSearchResult;
  defaultTab?: TabType;
}

type TabType = 'traditional' | 'commons';

export default function ComposerDrawer({
  open,
  onClose,
  defaultPerson,
  defaultField,
  defaultTab
}: ComposerDrawerProps) {
  const [activeTab, setActiveTab] = useState<TabType>(defaultTab || (defaultField ? 'commons' : 'traditional'));
  const [selectedPerson, setSelectedPerson] = useState<PersonSearchResult | null>(defaultPerson || null);
  const [selectedField, setSelectedField] = useState<FieldSearchResult | null>(defaultField || null);
  const [personQuery, setPersonQuery] = useState('');
  const [fieldQuery, setFieldQuery] = useState('');
  const [people, setPeople] = useState<PersonSearchResult[]>([]);
  const [fields, setFields] = useState<FieldSearchResult[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [expiry, setExpiry] = useState('');
  const [warnings, setWarnings] = useState<DelegationWarnings>({});
  const { success, error: showError } = useToast();

  // Calculate default expiry (4 years from now)
  const defaultExpiry = new Date();
  defaultExpiry.setFullYear(defaultExpiry.getFullYear() + 4);

  useEffect(() => {
    if (open) {
      if (defaultPerson) {
        setSelectedPerson(defaultPerson);
        setActiveTab('traditional');
      }
      if (defaultField) {
        setSelectedField(defaultField);
        setActiveTab('commons');
      }
      if (defaultTab) {
        setActiveTab(defaultTab);
      }
      if (activeTab === 'traditional' && !expiry) {
        setExpiry(defaultExpiry.toISOString().split('T')[0]);
      }
    }
  }, [open, defaultPerson, defaultField, defaultTab, activeTab, expiry]);

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

  const handleSubmit = async () => {
    if (!selectedPerson) {
      showError('Please select a person to delegate to');
      return;
    }

    if (activeTab === 'commons' && !selectedField) {
      showError('Please select a field for delegation');
      return;
    }

    setSubmitting(true);
    setWarnings({});

    try {
      const input: CreateDelegationInput = {
        mode: activeTab,
        delegatee_id: selectedPerson.id,
        field_id: selectedField?.id,
        expiry: expiry || undefined,
      };

      const response = await createDelegation(input);

      // Check for warnings in the response
      if (response.warnings) {
        setWarnings(response.warnings);
      }

      // Track delegation creation
      trackDelegationCreated(activeTab);

      success(
        activeTab === 'traditional'
          ? `Successfully delegated all power to ${selectedPerson.displayName}`
          : `Successfully delegated ${selectedField?.label} to ${selectedPerson.displayName}`
      );

      onClose();
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

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="absolute right-0 top-0 h-full w-full max-w-lg bg-surface border-l border-border shadow-xl transform transition-transform duration-300 ease-in-out">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <h2 className="text-xl font-semibold text-fg-strong">Create Delegation</h2>
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
              onClick={() => {
                console.log('Traditional tab clicked');
                setActiveTab('traditional');
              }}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors cursor-pointer ${
                activeTab === 'traditional'
                  ? 'text-primary-600 border-b-2 border-primary-600 bg-blue-50'
                  : 'text-fg-muted hover:text-fg hover:bg-gray-50'
              }`}
            >
              Delegate All (Traditional)
            </button>
            <button
              onClick={() => {
                console.log('Commons tab clicked');
                setActiveTab('commons');
              }}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors cursor-pointer ${
                activeTab === 'commons'
                  ? 'text-primary-600 border-b-2 border-primary-600 bg-blue-50'
                  : 'text-fg-muted hover:text-fg hover:bg-gray-50'
              }`}
            >
              Delegate by Field (Commons)
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Constitutional Warnings */}
            {(warnings.concentration || warnings.superDelegateRisk) && (
              <div className="mb-6 space-y-3">
                {warnings.concentration && (
                  <div className="p-3 bg-warn-bg border border-warn-fg/20 rounded-lg">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-warn-fg mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm text-warn-fg">
                          <strong>High concentration:</strong> ~{(warnings.concentration.percent * 100).toFixed(1)}% of delegations in this field go to this person.
                        </p>
                        <a 
                          href="/docs/cascade_rules.md" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs text-warn-fg/80 hover:text-warn-fg underline mt-1 inline-block"
                        >
                          Learn more
                        </a>
                      </div>
                    </div>
                  </div>
                )}
                {warnings.superDelegateRisk && (
                  <div className="p-3 bg-warn-bg border border-warn-fg/20 rounded-lg">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-warn-fg mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm text-warn-fg">
                          <strong>Super-delegate:</strong> This could create a 'super-delegate' pattern: {warnings.superDelegateRisk.reason}
                        </p>
                        <a 
                          href="/docs/cascade_rules.md" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs text-warn-fg/80 hover:text-warn-fg underline mt-1 inline-block"
                        >
                          Learn more
                        </a>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'traditional' ? (
              /* Traditional Tab */
              <div className="space-y-6">
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
                    <div className="mt-2 space-y-1">
                      {people.map((person) => (
                        <button
                          key={person.id}
                          onClick={() => {
                            setSelectedPerson(person);
                            setPersonQuery('');
                            setPeople([]);
                          }}
                          className="w-full p-3 text-left bg-surface-muted border border-border rounded-lg hover:bg-surface-muted/80 transition-colors"
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
                    <div className="mt-3 p-3 bg-ok-bg border border-ok-fg/20 rounded-lg">
                      <div className="font-medium text-ok-fg">{selectedPerson.displayName}</div>
                      {selectedPerson.bio && (
                        <div className="text-sm text-ok-fg/80">{selectedPerson.bio}</div>
                      )}
                    </div>
                  )}
                </div>

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
                    Expires: {formatExpiryDate(expiry)}
                  </p>
                </div>

                <div className="p-3 bg-info-bg border border-info-fg/20 rounded-lg">
                  <p className="text-sm text-info-fg">
                    <strong>Revocable anytime</strong> - You can revoke this delegation at any time.
                  </p>
                </div>
              </div>
            ) : (
              /* Commons Tab */
              <div className="space-y-6">
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
                    <div className="mt-2 space-y-1">
                      {fields.map((field) => (
                        <button
                          key={field.id}
                          onClick={() => {
                            setSelectedField(field);
                            setFieldQuery('');
                            setFields([]);
                          }}
                          className="w-full p-3 text-left bg-surface-muted border border-border rounded-lg hover:bg-surface-muted/80 transition-colors"
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
                    <div className="mt-3 p-3 bg-ok-bg border border-ok-fg/20 rounded-lg">
                      <div className="font-medium text-ok-fg">{selectedField.label}</div>
                      {selectedField.description && (
                        <div className="text-sm text-ok-fg/80">{selectedField.description}</div>
                      )}
                    </div>
                  )}
                </div>

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
                    <div className="mt-2 space-y-1">
                      {people.map((person) => (
                        <button
                          key={person.id}
                          onClick={() => {
                            setSelectedPerson(person);
                            setPersonQuery('');
                            setPeople([]);
                          }}
                          className="w-full p-3 text-left bg-surface-muted border border-border rounded-lg hover:bg-surface-muted/80 transition-colors"
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
                    <div className="mt-3 p-3 bg-ok-bg border border-ok-fg/20 rounded-lg">
                      <div className="font-medium text-ok-fg">{selectedPerson.displayName}</div>
                      {selectedPerson.bio && (
                        <div className="text-sm text-ok-fg/80">{selectedPerson.bio}</div>
                      )}
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-fg-strong mb-2">
                    Optional Expiry
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
                    {expiry ? `Expires: ${formatExpiryDate(expiry)}` : 'No expiry set'}
                  </p>
                </div>

                {/* Preview */}
                {selectedPerson && selectedField && (
                  <div className="p-4 bg-surface-muted border border-border rounded-lg">
                    <h4 className="font-medium text-fg-strong mb-2">Preview</h4>
                    <p className="text-sm text-fg-muted">
                      You will delegate: <strong>You → {selectedPerson.displayName}</strong>
                    </p>
                    <p className="text-sm text-fg-muted">
                      Scope: <strong>{selectedField.label}</strong>
                    </p>
                    <p className="text-sm text-fg-muted">
                      Expiry: <strong>{expiry ? formatExpiryDate(expiry) : 'None'}</strong>
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-border">
            <Button
              onClick={handleSubmit}
              disabled={!selectedPerson || (activeTab === 'commons' && !selectedField) || submitting}
              loading={submitting}
              className="w-full"
            >
              {activeTab === 'traditional'
                ? `Delegate all to ${selectedPerson?.displayName || 'Person'}`
                : 'Delegate for this field'
              }
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
