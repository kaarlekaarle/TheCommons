import React from "react";
import type { PersonSearchResult } from "../api/delegationsApi";

type Props = {
  items: PersonSearchResult[];
  onSelect: (person: PersonSearchResult) => void;
  emptyHint?: string;
};

export const PeopleSearchResults: React.FC<Props> = ({ items, onSelect, emptyHint }) => {
  if (!items.length) {
    return <p className="text-sm text-gray-500">{emptyHint ?? "No people found."}</p>;
  }
  return (
    <ul className="divide-y divide-gray-100 rounded-xl border border-gray-100 bg-white">
      {items.map(p => (
        <li key={p.id} className="flex items-center gap-3 p-3">
          {p.avatarUrl ? (
            <img src={p.avatarUrl} alt="" className="h-8 w-8 rounded-full object-cover" />
          ) : (
            <div className="h-8 w-8 rounded-full bg-gray-200" />
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium">{p.displayName}</span>
              {typeof p.trustScore === "number" && (
                <span className="text-xs text-gray-500">Trust {(p.trustScore * 100).toFixed(0)}%</span>
              )}
            </div>
            {p.bio && <p className="text-xs text-gray-500 truncate">{p.bio}</p>}
            {p.domains?.length ? (
              <div className="mt-1 flex flex-wrap gap-1">
                {p.domains.map(d => (
                  <span key={d} className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{d}</span>
                ))}
              </div>
            ) : null}
          </div>
          <button
            onClick={() => onSelect(p)}
            className="rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50"
          >
            Delegate
          </button>
        </li>
      ))}
    </ul>
  );
};
