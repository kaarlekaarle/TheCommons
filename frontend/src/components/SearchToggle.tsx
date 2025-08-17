import React from "react";

type Props = {
  value: "people" | "fields";
  onChange: (v: "people" | "fields") => void;
};

export const SearchToggle: React.FC<Props> = ({ value, onChange }) => (
  <div className="inline-flex rounded-xl bg-gray-100 p-1 text-sm">
    {(["people", "fields"] as const).map(opt => (
      <button
        key={opt}
        onClick={() => onChange(opt)}
        className={`px-3 py-1 rounded-lg transition
          ${value === opt ? "bg-white shadow text-gray-900" : "text-gray-600 hover:text-gray-900"}`}
        aria-pressed={value === opt}
      >
        {opt === "people" ? "People" : "Fields"}
      </button>
    ))}
  </div>
);
