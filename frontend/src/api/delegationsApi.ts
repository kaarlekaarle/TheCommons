// --- Search result types ---
export type PersonSearchResult = {
  id: string;
  displayName: string;
  bio?: string;
  avatarUrl?: string;
  trustScore?: number;   // 0..1 optional
  domains?: string[];    // domains they're known/trusted in
};

export type FieldSearchResult = {
  id: string;            // domain/label/principle id
  key: string;           // e.g., "environment"
  label: string;         // e.g., "Environment"
  description?: string;
  trending?: boolean;
};

// --- Delegation creation types ---
export type CreateDelegationInput = {
  mode: 'traditional' | 'field' | 'commons';
  delegatee_id: string;
  field_id?: string;
  expiry?: string; // ISO date string
};

export type DelegationWarnings = {
  concentration?: { 
    level: 'warn' | 'high'; 
    percent: number; 
  };
  superDelegateRisk?: { 
    reason: string; 
  };
};

export interface Delegation {
  id: string;
  delegator_id: string;
  delegatee_id: string;
  mode: string;
  target_type: string;
  field_id?: string;
  created_at: string;
  expires_at?: string;
  is_active: boolean;
}

export type CreateDelegationResponse = { 
  delegation: Delegation; 
  warnings?: DelegationWarnings; 
};

// --- Search endpoints ---
// NOTE: these can hit your real backend later.
// For now they'll call mock endpoints if not present.
export async function searchPeople(q: string): Promise<PersonSearchResult[]> {
  if (!q?.trim()) return [];
  const res = await fetch(`/api/search/people?q=${encodeURIComponent(q)}`);
  if (res.ok) return res.json();
  // fallback mock
  return [
    { id: "u_alice", displayName: "Alice", bio: "Economy, budgets", trustScore: 0.82, domains: ["economy"] },
    { id: "u_bob", displayName: "Bob", bio: "Climate & biodiversity", trustScore: 0.77, domains: ["environment"] },
  ].filter(p => p.displayName.toLowerCase().includes(q.toLowerCase()));
}

export async function searchFields(q: string): Promise<FieldSearchResult[]> {
  if (!q?.trim()) return [];
  const res = await fetch(`/api/search/fields?q=${encodeURIComponent(q)}`);
  if (res.ok) return res.json();
  // fallback mock
  const all: FieldSearchResult[] = [
    { id: "d_env", key: "environment", label: "Environment", description: "Climate, biodiversity" },
    { id: "d_econ", key: "economy", label: "Economy", description: "Budgets, taxation" },
    { id: "v_justice", key: "justice", label: "Justice (value)", description: "Value-as-delegate" },
  ];
  return all.filter(f =>
    f.label.toLowerCase().includes(q.toLowerCase()) ||
    f.key.toLowerCase().includes(q.toLowerCase())
  );
}

export async function getCombinedSearch(q: string): Promise<{ people: PersonSearchResult[]; fields: FieldSearchResult[] }> {
  if (!q?.trim()) return { people: [], fields: [] };
  
  try {
    // Fetch both people and fields in parallel
    const [peopleRes, fieldsRes] = await Promise.all([
      fetch(`/api/search/people?q=${encodeURIComponent(q)}`),
      fetch(`/api/search/fields?q=${encodeURIComponent(q)}`)
    ]);
    
    const people = peopleRes.ok ? await peopleRes.json() : [];
    const fields = fieldsRes.ok ? await fieldsRes.json() : [];
    
    return { people, fields };
  } catch (err) {
    // Fallback to mock data if API calls fail
    const mockPeople = await searchPeople(q);
    const mockFields = await searchFields(q);
    return { people: mockPeople, fields: mockFields };
  }
}

// --- Delegation creation endpoint ---
export async function createDelegation(input: CreateDelegationInput): Promise<CreateDelegationResponse> {
  const res = await fetch('/api/delegations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to create delegation' }));
    throw new Error(error.detail || 'Failed to create delegation');
  }

  return res.json();
}

// --- Transparency endpoints ---
export async function getMyChains(): Promise<any> {
  const res = await fetch('/api/delegations/me/chain');
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to fetch delegation chains' }));
    throw new Error(error.detail || 'Failed to fetch delegation chains');
  }
  return res.json();
}

export async function getInbound(delegateeId: string, fieldId?: string): Promise<any> {
  const params = new URLSearchParams();
  if (fieldId) params.append('fieldId', fieldId);
  
  const res = await fetch(`/api/delegations/${delegateeId}/inbound?${params.toString()}`);
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to fetch inbound delegations' }));
    throw new Error(error.detail || 'Failed to fetch inbound delegations');
  }
  return res.json();
}

export async function getHealthSummary(): Promise<any> {
  const res = await fetch('/api/delegations/health/summary');
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to fetch health summary' }));
    throw new Error(error.detail || 'Failed to fetch health summary');
  }
  return res.json();
}

// --- Telemetry endpoints ---
export async function trackComposerOpen(mode: string): Promise<void> {
  try {
    await fetch('/api/telemetry/composer-open', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ mode }),
    });
  } catch (err) {
    // Silently fail - telemetry is non-critical
    console.debug('Failed to track composer open:', err);
  }
}

export async function trackDelegationCreated(mode: string): Promise<void> {
  try {
    await fetch('/api/telemetry/delegation-created', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ mode }),
    });
  } catch (err) {
    // Silently fail - telemetry is non-critical
    console.debug('Failed to track delegation created:', err);
  }
}

export async function getMyAdoptionSnapshot(): Promise<{
  last30d: { legacyPct: number; commonsPct: number };
}> {
  try {
    const res = await fetch('/api/delegations/adoption/stats?days=30');
    if (!res.ok) {
      throw new Error('Failed to fetch adoption stats');
    }
    const data = await res.json();
    
    return {
      last30d: {
        legacyPct: data.mode_percentages?.legacy_fixed_term || 0,
        commonsPct: data.mode_percentages?.flexible_domain || 0,
      }
    };
  } catch (err) {
    console.debug('Failed to fetch adoption snapshot:', err);
    // Return neutral defaults if API fails
    return {
      last30d: { legacyPct: 0, commonsPct: 0 }
    };
  }
}
