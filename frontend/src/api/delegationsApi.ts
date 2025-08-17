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
