import api from '../lib/api';

// --- Delegation summary types ---
export interface DelegationSummary {
  ok: boolean;
  counts: { mine: number; inbound: number };
  adoption?: { commonsPct: number; legacyPct: number; transitions?: number };
  meta?: { errors?: string[]; trace_id?: string; generated_at?: string };
}

export interface Delegation {
  id: string;
  mode: 'LEGACY_FIXED_TERM' | 'FLEXIBLE_DOMAIN' | 'HYBRID_SEED';
  fieldId?: string | null;
  personId: string;
  expiresAt?: string | null; // ISO
}

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



export type CreateDelegationResponse = {
  delegation: Delegation;
  warnings?: DelegationWarnings;
};

// --- Safe parsers ---
function parseSummary(x: unknown): DelegationSummary {
  const d = x as any; // eslint-disable-line @typescript-eslint/no-explicit-any
  return {
    ok: Boolean(d?.ok),
    counts: {
      mine: Number(d?.counts?.mine ?? 0),
      inbound: Number(d?.counts?.inbound ?? 0),
    },
    adoption: d?.adoption && {
      commonsPct: Number(d.adoption.commonsPct ?? 0),
      legacyPct: Number(d.adoption.legacyPct ?? 0),
      transitions: d.adoption.transitions != null ? Number(d.adoption.transitions) : undefined,
    },
    meta: d?.meta && {
      generated_at: d.meta.generated_at ? String(d.meta.generated_at) : undefined,
      errors: Array.isArray(d.meta.errors) ? d.meta.errors : undefined,
      trace_id: d.meta.trace_id ? String(d.meta.trace_id) : undefined,
    },
  };
}

export async function fetchDelegationSummary(): Promise<DelegationSummary> {
  try {
    const r = await fetch('/api/delegations/summary');
    const j = await r.json().catch(() => ({}));
    return parseSummary(j);
  } catch (e: unknown) {
    const error = e as { message?: string };
    return { ok: false, counts: { mine: 0, inbound: 0 }, meta: { errors: [error?.message ?? 'fetch failed'] } };
  }
}

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
  } catch {
    // Fallback to mock data if API calls fail
    const mockPeople = await searchPeople(q);
    const mockFields = await searchFields(q);
    return { people: mockPeople, fields: mockFields };
  }
}

// --- Delegation creation endpoint ---
export async function createDelegation(input: CreateDelegationInput): Promise<CreateDelegationResponse> {
  try {
    const response = await api.post('/api/delegations', input);
    return response.data;
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } };
    throw new Error(err.response?.data?.detail || 'Failed to create delegation');
  }
}

// --- Transparency endpoints ---
export async function getMyChains(): Promise<any> {
  try {
    const response = await api.get('/api/delegations/me/chain');
    return response.data;
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } };
    throw new Error(err.response?.data?.detail || 'Failed to fetch delegation chains');
  }
}

export async function getInbound(delegateeId: string, fieldId?: string): Promise<any> {
  try {
    const params = new URLSearchParams();
    if (fieldId) params.append('fieldId', fieldId);

    const response = await api.get(`/api/delegations/${delegateeId}/inbound?${params.toString()}`);
    return response.data;
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } };
    throw new Error(err.response?.data?.detail || 'Failed to fetch inbound delegations');
  }
}

export async function getHealthSummary(): Promise<any> {
  try {
    const response = await api.get('/api/delegations/health/summary');
    return response.data;
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } };
    throw new Error(err.response?.data?.detail || 'Failed to fetch health summary');
  }
}

// --- Telemetry endpoints ---
export async function trackComposerOpen(mode: string): Promise<void> {
  try {
    await api.post('/api/telemetry/composer-open', { mode });
  } catch (err) {
    // Silently fail - telemetry is non-critical
    console.debug('Failed to track composer open:', err);
  }
}

export async function trackDelegationCreated(mode: string): Promise<void> {
  try {
    await api.post('/api/telemetry/delegation-created', { mode });
  } catch (err) {
    // Silently fail - telemetry is non-critical
    console.debug('Failed to track delegation created:', err);
  }
}

export async function trackDelegationSummaryLoaded(ok: boolean): Promise<void> {
  try {
    await api.post('/api/telemetry/delegation-summary-loaded', { ok });
  } catch (err) {
    // Silently fail - telemetry is non-critical
    console.debug('Failed to track delegation summary loaded:', err);
  }
}

export async function getMyAdoptionSnapshot(): Promise<{
  last30d: { legacyPct: number; commonsPct: number };
}> {
  try {
    const response = await api.get('/api/delegations/adoption/stats?days=30');
    const data = response.data;

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
