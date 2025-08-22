import { useState } from "react";

export function Expandable({
  children,
  defaultOpen = false,
  id
}: {
  children: React.ReactNode;
  defaultOpen?: boolean;
  id?: string
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="mt-3">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen(o => !o)}
        className="text-sm font-medium text-blue-700 hover:underline focus-ring inline-flex items-center gap-1"
      >
        {open ? "Hide details" : "Read more"}
        <span aria-hidden className={`transition-transform ${open ? 'rotate-180' : ''}`}>▾</span>
      </button>
      {open && (
        <div id={id} className="mt-2 text-sm text-gray-700">
          {children}
        </div>
      )}
    </div>
  );
}
