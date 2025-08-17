import React, { useState, useEffect, useRef } from "react";
import InlineTraditionalForm from "../components/delegations/InlineTraditionalForm";
import InlineCommonsForm from "../components/delegations/InlineCommonsForm";
import TransparencyPanel from "../components/delegations/TransparencyPanel";
import type { PersonSearchResult, FieldSearchResult } from "../api/delegationsApi";
import { trackComposerOpen, trackDelegationCreated, getMyAdoptionSnapshot, getCombinedSearch } from "../api/delegationsApi";
import { AlertTriangle, AlertCircle, Search, User, Hash, ChevronDown, ChevronUp } from "lucide-react";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";

interface CascadeHealth {
  ruleB: string;
  effectiveBlockMs: number | null;
  p95Ms: number | null;
}

export default function DelegationsPage() {
  const [query, setQuery] = useState("");
  const [people, setPeople] = useState<PersonSearchResult[]>([]);
  const [fields, setFields] = useState<FieldSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [openCard, setOpenCard] = useState<'traditional' | 'commons' | null>(null);
  const [selectedPerson, setSelectedPerson] = useState<PersonSearchResult | undefined>(undefined);
  const [selectedField, setSelectedField] = useState<FieldSearchResult | undefined>(undefined);
  const [cascadeHealth, setCascadeHealth] = useState<CascadeHealth | null>(null);
  const [peopleWarnings, setPeopleWarnings] = useState<Record<string, { concentration?: boolean; superDelegate?: boolean }>>({});
  const [transparencyOpen, setTransparencyOpen] = useState(false);
  const [adoptionSnapshot, setAdoptionSnapshot] = useState<{ last30d: { legacyPct: number; commonsPct: number } } | null>(null);

  // Fetch cascade health on mount
  useEffect(() => {
    async function fetchCascadeHealth() {
      try {
        const response = await fetch('/api/health/cascade');
        if (response.ok) {
          const data = await response.json();
          setCascadeHealth(data);
        } else {
          console.warn('Cascade health endpoint returned non-OK status:', response.status);
          // Set a default state to prevent errors
          setCascadeHealth({
            ruleB: "unknown",
            effectiveBlockMs: null,
            p95Ms: null
          });
        }
      } catch (err) {
        console.error('Failed to fetch cascade health:', err);
        // Set a default state to prevent errors
        setCascadeHealth({
          ruleB: "unknown",
          effectiveBlockMs: null,
          p95Ms: null
        });
      }
    }

    fetchCascadeHealth();
  }, []);

  // Fetch adoption snapshot on mount
  useEffect(() => {
    async function fetchAdoptionSnapshot() {
      try {
        const snapshot = await getMyAdoptionSnapshot();
        setAdoptionSnapshot(snapshot);
      } catch (err) {
        console.error('Failed to fetch adoption snapshot:', err);
      }
    }

    fetchAdoptionSnapshot();
  }, []);

  const handlePersonClick = (person: PersonSearchResult) => {
    setSelectedPerson(person);
    setSelectedField(undefined);
    setOpenCard('traditional');
    // Track composer open with traditional mode pre-selected
    trackComposerOpen('traditional');
  };

  const handleFieldClick = (field: FieldSearchResult) => {
    setSelectedField(field);
    setSelectedPerson(undefined);
    setOpenCard('commons');
    // Track composer open with commons mode pre-selected
    trackComposerOpen('commons');
  };

  const handleCollapseForm = () => {
    setOpenCard(null);
    setSelectedPerson(undefined);
    setSelectedField(undefined);
  };

  // Combined search with debounce
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!query.trim()) {
      setPeople([]);
      setFields([]);
      setShowResults(false);
      setSelectedIndex(-1);
      return;
    }

    setLoading(true);
    setError(null);

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const results = await getCombinedSearch(query);
        setPeople(results.people);
        setFields(results.fields);
        setShowResults(true);
        setSelectedIndex(-1);
      } catch (err: any) {
        setError(err.message || 'Search failed');
        setPeople([]);
        setFields([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [query]);

  // Keyboard support for Escape key to collapse forms
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && openCard) {
        handleCollapseForm();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [openCard]);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    const totalItems = people.length + fields.length;
    
    if (totalItems === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < totalItems - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : totalItems - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          const itemIndex = selectedIndex;
          if (itemIndex < people.length) {
            handlePersonClick(people[itemIndex]);
          } else {
            const fieldIndex = itemIndex - people.length;
            handleFieldClick(fields[fieldIndex]);
          }
        }
        break;
      case 'Escape':
        setShowResults(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const handleItemClick = (type: 'person' | 'field', item: PersonSearchResult | FieldSearchResult) => {
    if (type === 'person') {
      handlePersonClick(item as PersonSearchResult);
    } else {
      handleFieldClick(item as FieldSearchResult);
    }
    setShowResults(false);
    setQuery("");
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.search-container')) {
        setShowResults(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Check if performance banner should be shown
  const showPerformanceBanner = cascadeHealth &&
    cascadeHealth.ruleB === "high" &&
    cascadeHealth.effectiveBlockMs &&
    cascadeHealth.p95Ms &&
    cascadeHealth.effectiveBlockMs >= 1550 &&
    cascadeHealth.p95Ms >= 1480;

  // Fetch warnings for people when search results change
  useEffect(() => {
    if (people.length > 0) {
      fetchPeopleWarnings();
    }
  }, [people]);

  const fetchPeopleWarnings = async () => {
    const warnings: Record<string, { concentration?: boolean; superDelegate?: boolean }> = {};
    
    // Fetch inbound delegations for each person to check for warnings
    for (const person of people) {
      try {
        const response = await fetch(`/api/delegations/${person.id}/inbound?limit=1`);
        if (response.ok) {
          const data = await response.json();
          // Simple heuristic: if they have many inbound delegations, show warning
          if (data.counts.total > 10) {
            warnings[person.id] = { concentration: true };
          }
          if (data.counts.total > 50) {
            warnings[person.id] = { ...warnings[person.id], superDelegate: true };
          }
        }
      } catch (err) {
        // Silently fail - warnings are optional
        console.debug('Failed to fetch warnings for person:', person.id);
      }
    }
    
    setPeopleWarnings(warnings);
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      {/* Performance Banner */}
      {showPerformanceBanner && (
        <div className="mb-6 p-4 bg-warn-bg border border-warn-fg/20 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-warn-fg mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-medium text-warn-fg mb-1">Performance Notice</h3>
              <p className="text-sm text-warn-fg/80">
                Performance near threshold (p95 {cascadeHealth.p95Ms?.toFixed(2) || 'unknown'}s). Overrides may feel slower.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Your Delegation Mode Nudge */}
      {adoptionSnapshot && (adoptionSnapshot.last30d.legacyPct > 0 || adoptionSnapshot.last30d.commonsPct > 0) && (
        <Card className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-fg-strong mb-1">Your delegation mode</h3>
              <p className="text-sm text-fg-muted">
                {adoptionSnapshot.last30d.legacyPct > adoptionSnapshot.last30d.commonsPct ? (
                  "You're mostly using Traditional (4-year) delegations. Curious to try domain-based, revocable Commons?"
                ) : (
                  "You're mostly using Commons (by field, revocable). Prefer one person for everything?"
                )}
              </p>
            </div>
            <Button
              onClick={() => {
                const suggestedTab = adoptionSnapshot.last30d.legacyPct > adoptionSnapshot.last30d.commonsPct ? 'commons' : 'traditional';
                setOpenCard(suggestedTab);
                setSelectedPerson(undefined);
                setSelectedField(undefined);
                // Track the nudge click
                trackComposerOpen(suggestedTab);
              }}
              size="sm"
            >
              {adoptionSnapshot.last30d.legacyPct > adoptionSnapshot.last30d.commonsPct ? (
                "Try Commons delegation"
              ) : (
                "Create 4-year delegation"
              )}
            </Button>
          </div>
        </Card>
      )}

      {/* Page Title */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold text-fg-strong">Delegations</h1>
        <Button onClick={() => setTransparencyOpen(true)}>
          Transparency
        </Button>
      </div>

      {/* Transition Banner */}
      <div className="mt-6 p-6 bg-surface border border-border rounded-lg">
        <h2 className="text-lg font-medium text-fg-strong mb-4">Choose Your Delegation Approach</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="p-4 bg-surface-muted border border-border rounded-lg">
            <h3 id="traditional-title" className="font-medium text-fg-strong mb-2">Traditional</h3>
            <p className="text-fg-muted text-sm mb-4">Delegate all power to one person for 4 years (revocable).</p>
            
            {openCard === 'traditional' ? (
              <InlineTraditionalForm
                onSubmitted={handleCollapseForm}
                defaults={{
                  personId: selectedPerson?.id,
                  termDate: new Date(Date.now() + 4 * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
                }}
                onCollapse={handleCollapseForm}
              />
            ) : (
              <button
                onClick={() => {
                  setOpenCard('traditional');
                  setSelectedPerson(undefined);
                  setSelectedField(undefined);
                  trackComposerOpen('traditional');
                }}
                className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Create Traditional Delegation
              </button>
            )}
          </div>
          
          <div className="p-4 bg-info-bg border border-border rounded-lg">
            <h3 id="commons-title" className="font-medium text-fg-strong mb-2">Commons</h3>
            <p className="text-fg-muted text-sm mb-4">Delegate by field, interrupt anytime.</p>
            
            {openCard === 'commons' ? (
              <InlineCommonsForm
                onSubmitted={handleCollapseForm}
                defaults={{
                  fieldId: selectedField?.id,
                  personId: selectedPerson?.id,
                  expiryDate: null
                }}
                onCollapse={handleCollapseForm}
              />
            ) : (
              <button
                onClick={() => {
                  setOpenCard('commons');
                  setSelectedPerson(undefined);
                  setSelectedField(undefined);
                  trackComposerOpen('commons');
                }}
                className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                Create Commons Delegation
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Combined Search Input */}
      <div className="mt-6 relative search-container">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-fg-muted" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowResults(true)}
            placeholder="Search people or fields…"
            className="w-full max-w-2xl pl-10 pr-4 py-3 border border-border rounded-lg bg-surface text-fg placeholder-placeholder focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
          />
        </div>
        
        {/* Search Results Dropdown */}
        {showResults && (query.trim() || loading) && (
          <div className="absolute top-full left-0 right-0 max-w-2xl mt-1 bg-surface border border-border rounded-lg shadow-lg z-10 max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-4">
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex items-center space-x-3 p-3 animate-pulse">
                      <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : error ? (
              <div className="p-4 text-danger-fg text-sm">
                {error}
              </div>
            ) : people.length === 0 && fields.length === 0 ? (
              <div className="p-4 text-fg-muted text-sm text-center">
                No results found
              </div>
            ) : (
              <div className="p-2">
                {/* People Section */}
                {people.length > 0 && (
                  <div className="mb-4">
                    <div className="px-3 py-2 text-xs font-medium text-fg-muted uppercase tracking-wide">
                      People
                    </div>
                    <div className="space-y-1">
                      {people.map((person, index) => (
                        <button
                          key={person.id}
                          onClick={() => handleItemClick('person', person)}
                          className={`w-full p-3 rounded-lg text-left transition-colors flex items-center space-x-3 ${
                            selectedIndex === index
                              ? 'bg-primary-100 border-primary-500'
                              : 'hover:bg-surface-muted'
                          }`}
                        >
                          <User className="w-5 h-5 text-fg-muted flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-fg-strong truncate">
                              {person.displayName}
                            </div>
                            {person.bio && (
                              <div className="text-sm text-fg-muted truncate">
                                {person.bio}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-1 flex-shrink-0">
                            {peopleWarnings[person.id]?.concentration && (
                              <AlertTriangle className="w-4 h-4 text-warn-fg" />
                            )}
                            {peopleWarnings[person.id]?.superDelegate && (
                              <AlertCircle className="w-4 h-4 text-danger-fg" />
                            )}
                            {selectedIndex === index && (
                              <ChevronDown className="w-4 h-4 text-primary-600" />
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Fields Section */}
                {fields.length > 0 && (
                  <div>
                    <div className="px-3 py-2 text-xs font-medium text-fg-muted uppercase tracking-wide">
                      Fields
                    </div>
                    <div className="space-y-1">
                      {fields.map((field, index) => (
                        <button
                          key={field.id}
                          onClick={() => handleItemClick('field', field)}
                          className={`w-full p-3 rounded-lg text-left transition-colors flex items-center space-x-3 ${
                            selectedIndex === people.length + index
                              ? 'bg-primary-100 border-primary-500'
                              : 'hover:bg-surface-muted'
                          }`}
                        >
                          <Hash className="w-5 h-5 text-fg-muted flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-fg-strong truncate">
                              {field.label}
                            </div>
                            {field.description && (
                              <div className="text-sm text-fg-muted truncate">
                                {field.description}
                              </div>
                            )}
                          </div>
                          {selectedIndex === people.length + index && (
                            <ChevronDown className="w-4 h-4 text-primary-600" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        
        {error && (
          <p className="mt-2 text-sm text-danger-fg">{error}</p>
        )}
      </div>

      {/* Transparency Panel */}
      <TransparencyPanel
        isOpen={transparencyOpen}
        onClose={() => setTransparencyOpen(false)}
      />
    </div>
  );
}
