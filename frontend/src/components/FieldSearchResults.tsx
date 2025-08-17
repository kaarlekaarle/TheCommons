import React from "react";
import type { FieldSearchResult } from "../api/delegationsApi";

type Props = {
  items: FieldSearchResult[];
  onSelect: (field: FieldSearchResult) => void;
  emptyHint?: string;
};

export const FieldSearchResults: React.FC<Props> = ({ items, onSelect, emptyHint }) => {
  if (!items.length) {
    return <p className="text-sm text-gray-500">{emptyHint ?? "No fields found."}</p>;
  }
  return (
    <ul className="divide-y divide-gray-100 rounded-xl border border-gray-100 bg-white">
      {items.map(f => (
        <li key={f.id} className="flex items-center justify-between gap-3 p-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium">{f.label}</span>
              {f.trending && <span className="text-xs rounded-full bg-amber-100 px-2 py-0.5 text-amber-700">trending</span>}
            </div>
            {f.description && <p className="text-xs text-gray-500 truncate">{f.description}</p>}
          </div>
          <button
            onClick={() => onSelect(f)}
            className="rounded-lg border px-3 py-1.5 text-sm hover:bg-gray-50"
          >
            Explore
          </button>
        </li>
      ))}
    </ul>
  );
};
