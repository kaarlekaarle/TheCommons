import type { DomainDelegation } from '@/lib/delegations/types';

export function DomainCard({ domain }: { domain: DomainDelegation }) {
  const status = domain.status.join(' · ');
  const targetLabel = domain.target
    ? `${domain.target.name} (${domain.target.kind})`
    : 'Not delegated';

  return (
    <div className="rounded-2xl border bg-white p-4 shadow-sm">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="text-lg font-medium">{domain.domainName}</h3>
        <StatusChips statuses={domain.status} />
      </div>

      <div className="mb-3 text-sm text-gray-700">
        <span className="font-medium">Current:</span> {targetLabel}
        {domain.expiresAt && (
          <span className="ml-2 text-xs text-gray-500">
            · Expires {new Date(domain.expiresAt).toLocaleDateString()}
          </span>
        )}
        {domain.anonymity && <span className="ml-2 text-xs text-purple-700">· Anonymous</span>}
      </div>

      <div className="flex gap-2">
        <button
          className="rounded-xl border px-3 py-1.5 text-sm hover:bg-gray-50"
          // onClick={() => openManageModal(domain.domainId)}
          disabled
          title="Manage coming soon"
        >
          Manage
        </button>
        <button
          className="rounded-xl border px-3 py-1.5 text-sm hover:bg-gray-50"
          // onClick={() => openChainModal(domain.domainId)}
          disabled
          title="Chain coming soon"
        >
          View chain
        </button>
        <button
          className="ml-auto rounded-xl border px-3 py-1.5 text-sm text-red-700 hover:bg-red-50"
          // onClick={() => interrupt(domain.domainId)}
          disabled
          title="Interrupt coming soon"
        >
          Interrupt
        </button>
      </div>
    </div>
  );
}

function StatusChips({ statuses }: { statuses: DomainDelegation['status'] }) {
  const chip = (s: string) => {
    const style =
      s === 'active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
      s === 'expiring' ? 'bg-amber-50 text-amber-700 border-amber-200' :
      s === 'dormant' ? 'bg-slate-50 text-slate-700 border-slate-200' :
      'bg-rose-50 text-rose-700 border-rose-200';
    return (
      <span key={s} className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${style}`}>{s}</span>
    );
  };
  return <div className="flex gap-1.5">{statuses.map(chip)}</div>;
}
