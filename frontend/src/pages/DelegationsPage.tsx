import React from "react";
import { useUnifiedDelegationSearch } from "../hooks/useUnifiedDelegationSearch";

export default function DelegationsPage() {
  const { query, setQuery, people, fields, loading, error } = useUnifiedDelegationSearch();

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      {/* Page Title */}
      <h1 className="text-3xl font-semibold text-fg-strong">Delegations</h1>

      {/* Transition Banner */}
      <div className="mt-6 p-6 bg-surface border border-border rounded-lg">
        <h2 className="text-lg font-medium text-fg-strong mb-4">Choose Your Delegation Approach</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="p-4 bg-surface-muted border border-border rounded-lg">
            <h3 className="font-medium text-fg-strong mb-2">Traditional</h3>
            <p className="text-fg-muted text-sm">Delegate all power to one person for 4 years (revocable).</p>
          </div>
          <div className="p-4 bg-info-bg border border-border rounded-lg">
            <h3 className="font-medium text-fg-strong mb-2">Commons</h3>
            <p className="text-fg-muted text-sm">Delegate by field, interrupt anytime.</p>
          </div>
        </div>
      </div>

      {/* Unified Search Input */}
      <div className="mt-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search people or fields…"
          className="w-full max-w-2xl px-4 py-3 border border-border rounded-lg bg-surface text-fg placeholder-placeholder focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
        />
        {error && (
          <p className="mt-2 text-sm text-danger-fg">{error}</p>
        )}
      </div>

      {/* People and Fields Sections */}
      <div className="mt-8 grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-semibold text-fg-strong mb-4">People</h2>
          <div className="p-6 bg-surface border border-border rounded-lg min-h-[200px]">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              </div>
            ) : people.length > 0 ? (
              <div className="space-y-3">
                {people.map((person) => (
                  <div key={person.id} className="p-3 bg-surface-muted rounded-lg border border-border">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-fg-strong">{person.displayName}</h3>
                        {person.bio && (
                          <p className="text-sm text-fg-muted mt-1">{person.bio}</p>
                        )}
                      </div>
                      {person.trustScore && (
                        <span className="text-xs bg-ok-bg text-ok-fg px-2 py-1 rounded">
                          {Math.round(person.trustScore * 100)}%
                        </span>
                      )}
                    </div>
                    {person.domains && person.domains.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {person.domains.map((domain) => (
                          <span key={domain} className="text-xs bg-info-bg text-info-fg px-2 py-1 rounded">
                            {domain}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : query ? (
              <div className="text-center text-fg-muted py-8">
                <p>No people found</p>
              </div>
            ) : (
              <div className="text-center text-fg-muted py-8">
                <p>Try 'housing', 'energy', or 'climate'</p>
              </div>
            )}
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-fg-strong mb-4">Fields</h2>
          <div className="p-6 bg-surface border border-border rounded-lg min-h-[200px]">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              </div>
            ) : fields.length > 0 ? (
              <div className="space-y-3">
                {fields.map((field) => (
                  <div key={field.id} className="p-3 bg-surface-muted rounded-lg border border-border">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-fg-strong">{field.label}</h3>
                        {field.description && (
                          <p className="text-sm text-fg-muted mt-1">{field.description}</p>
                        )}
                      </div>
                      {field.trending && (
                        <span className="text-xs bg-warn-bg text-warn-fg px-2 py-1 rounded">
                          Trending
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : query ? (
              <div className="text-center text-fg-muted py-8">
                <p>No fields found</p>
              </div>
            ) : (
              <div className="text-center text-fg-muted py-8">
                <p>Try 'housing', 'energy', or 'climate'</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
