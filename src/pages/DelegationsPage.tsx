import { DomainCard } from '@/ui/delegations/DomainCard';
import type { DomainDelegation } from '@/lib/delegations/types';

const exampleDomains: DomainDelegation[] = [
  {
    domainId: 'economy',
    domainName: 'Economy',
    target: { kind: 'person', id: 'alice', name: 'Alice' },
    status: ['active'],
    expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 30).toISOString(),
  },
  {
    domainId: 'environment',
    domainName: 'Environment',
    target: { kind: 'person', id: 'bob', name: 'Bob' },
    status: ['active', 'expiring'],
    expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 24 * 7).toISOString(),
  },
  {
    domainId: 'healthcare',
    domainName: 'Healthcare',
    target: { kind: 'person', id: 'charlie', name: 'Charlie' },
    status: ['active'],
    anonymity: true,
  },
];

export default function DelegationsPage() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Your Delegations</h1>
        <p className="text-sm text-gray-600">
          Delegate per domain. You keep control: interrupt or revoke anytime.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        {exampleDomains.map((d) => (
          <DomainCard key={d.domainId} domain={d} />
        ))}
      </section>
    </div>
  );
}
