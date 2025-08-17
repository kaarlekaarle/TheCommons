import React, { useEffect, useState } from "react";
import { fetchDelegations } from '../lib/delegations/api';
import type { Delegation } from '../lib/delegations/types';
import { DomainCard } from '../ui/delegations/DomainCard';
import { searchPeople, searchFields } from "../api/delegationsApi";
import type { PersonSearchResult, FieldSearchResult } from "../api/delegationsApi";
import { useDebounce } from "../hooks/useDebounce";
import { PeopleSearchResults } from "../components/PeopleSearchResults";
import { FieldSearchResults } from "../components/FieldSearchResults";

export default function DelegationsPage() {
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [query, setQuery] = useState("");
  const dq = useDebounce(query, 250);

  const [people, setPeople] = useState<PersonSearchResult[]>([]);
  const [fields, setFields] = useState<FieldSearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDelegations().then(setDelegations);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (!dq.trim()) { setPeople([]); setFields([]); return; }
      setLoading(true);
      try {
        const [p, f] = await Promise.all([searchPeople(dq), searchFields(dq)]);
        if (!cancelled) { setPeople(p); setFields(f); }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => { cancelled = true; };
  }, [dq]);

  function handleSelectPerson(p: PersonSearchResult) {
    // open your existing ManageDelegationModal with target = person
    // e.g., openManageModal({ targetType: "person", targetId: p.id })
    alert(`Delegate to ${p.displayName} (person) — hook up to your modal`);
  }

  function handleSelectField(f: FieldSearchResult) {
    // "Explore" a field: maybe filter the cards below or open a value-as-delegate flow
    alert(`Explore field ${f.label} — hook up to your modal / field view`);
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="text-3xl font-semibold">Your Delegations</h1>
      <p className="mt-2 text-gray-600">Delegate per domain. You keep control: interrupt or revoke anytime.</p>

      {/* Search section */}
      <div className="mt-6 rounded-2xl border border-gray-100 bg-white p-4">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search for people or fields…"
          className="w-full rounded-xl border px-3 py-2 text-sm focus:outline-none focus:ring sm:max-w-lg"
        />

        {dq && (
          <div className="mt-4 space-y-6">
            <div>
              <h3 className="text-sm font-medium text-gray-700">People</h3>
              <PeopleSearchResults
                items={people}
                onSelect={handleSelectPerson}
                emptyHint="No people found."
              />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-700">Fields</h3>
              <FieldSearchResults
                items={fields}
                onSelect={handleSelectField}
                emptyHint="No fields found."
              />
            </div>
          </div>
        )}
      </div>

      {/* Domain cards section */}
      <div className="mt-8">
        <section className="grid gap-4 md:grid-cols-2">
          {delegations.map((d) => (
            <DomainCard key={d.domainName} domainName={d.domainName} delegatedTo={d.delegatedTo} />
          ))}
        </section>
      </div>
    </div>
  );
}
