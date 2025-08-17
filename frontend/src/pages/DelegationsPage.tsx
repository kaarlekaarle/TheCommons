import React, { useState } from "react";

export default function DelegationsPage() {
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      {/* Page Title */}
      <h1 className="text-3xl font-semibold text-fg-strong">Delegations</h1>

      {/* Transition Banner */}
      <div className="mt-6 p-6 bg-surface border border-border rounded-lg">
        <h2 className="text-lg font-medium text-fg-strong mb-4">Choose Your Delegation Approach</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="p-4 bg-surface-muted border border-border rounded-lg">
            <h3 className="font-medium text-fg-strong mb-2">Traditional</h3>
            <p className="text-fg-muted text-sm">Delegate all power to one person for 4 years (revocable).</p>
          </div>
          <div className="p-4 bg-info-bg border border-border rounded-lg">
            <h3 className="font-medium text-fg-strong mb-2">Commons</h3>
            <p className="text-fg-muted text-sm">Delegate by field, interrupt anytime.</p>
          </div>
        </div>
      </div>

      {/* Unified Search Input */}
      <div className="mt-6">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search people or fields…"
          className="w-full max-w-2xl px-4 py-3 border border-border rounded-lg bg-surface text-fg placeholder-placeholder focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent"
        />
      </div>

      {/* People and Fields Sections */}
      <div className="mt-8 grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-semibold text-fg-strong mb-4">People</h2>
          <div className="p-6 bg-surface border border-border rounded-lg min-h-[200px]">
            {/* Empty section for People */}
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-fg-strong mb-4">Fields</h2>
          <div className="p-6 bg-surface border border-border rounded-lg min-h-[200px]">
            {/* Empty section for Fields */}
          </div>
        </div>
      </div>
    </div>
  );
}
