import React, { useState } from "react";
import Button from "../components/ui/Button";
import { createProposal } from "../lib/api";
import { useNavigate } from "react-router-dom";

const LEVEL_A_CHOICES = [
  "Environmental issues: Fuck nature",
  "Environmental issues: Let's take care of nature",
];

// Feature flag for Level A decisions
const LEVEL_A_ENABLED = import.meta.env.VITE_LEVEL_A_ENABLED !== "false";

export default function ProposalNew() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const [decisionType, setDecisionType] = useState<"level_a" | "level_b">("level_b");
  const [directionChoice, setDirectionChoice] = useState<string>("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!title.trim()) return setError("Title is required.");
    if (!description.trim()) return setError("Description is required.");
    if (decisionType === "level_a" && !directionChoice) {
      return setError("Please choose one of the Level‑A directions.");
    }

    try {
      setSubmitting(true);
      const payload = {
        title: title.trim(),
        description: description.trim(),
        decision_type: decisionType,
        direction_choice: decisionType === "level_a" ? directionChoice : null,
      };
      const created = await createProposal(payload);
      navigate(`/proposals/${created.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.message || "Failed to create proposal.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="card">
        <div className="card-content space-y-6">
          <h1 className="text-2xl md:text-3xl font-semibold">Create Proposal</h1>

          {error && (
            <div className="border border-red-500/40 bg-red-500/10 text-red-300 rounded-lg p-3">
              {error}
            </div>
          )}

          {/* Decision Type Selector */}
          <div className="space-y-2">
            <label className="block text-sm text-muted">Decision type</label>
            <div className={`grid gap-3 ${LEVEL_A_ENABLED ? 'md:grid-cols-2' : 'md:grid-cols-1'}`}>
              {LEVEL_A_ENABLED && (
                <button
                  type="button"
                  onClick={() => setDecisionType("level_a")}
                  className={`rounded-xl border p-4 text-left transition-colors ${
                    decisionType === "level_a"
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-primary/40"
                  }`}
                >
                  <div className="font-semibold">Baseline Policy (Level A)</div>
                  <div className="text-sm text-muted">
                    High‑level, slow‑changing principle. Rarely updated.
                  </div>
                </button>
              )}

              <button
                type="button"
                onClick={() => setDecisionType("level_b")}
                className={`rounded-xl border p-4 text-left transition-colors ${
                  decisionType === "level_b"
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/40"
                }`}
              >
                <div className="font-semibold">Poll (Level B)</div>
                <div className="text-sm text-muted">
                  Quick action on a specific issue. Yes / No / Abstain.
                </div>
              </button>
            </div>
          </div>

          {/* Level A choices */}
          {decisionType === "level_a" && (
            <div className="space-y-3">
              <div className="text-sm text-muted">
                Choose the baseline direction to make the concept clear.
              </div>
              <div className="space-y-2">
                {LEVEL_A_CHOICES.map((c) => (
                  <label key={c} className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-primary/40 cursor-pointer">
                    <input
                      type="radio"
                      name="direction_choice"
                      className="accent-primary"
                      value={c}
                      checked={directionChoice === c}
                      onChange={() => setDirectionChoice(c)}
                    />
                    <span className="text-white">{c}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Title/Description */}
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-muted mb-1">Title</label>
              <input
                className="w-full rounded-lg bg-surface border border-border p-3 text-white outline-none focus:border-primary"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Short, clear title"
              />
            </div>
            <div>
              <label className="block text-sm text-muted mb-1">Description</label>
              <textarea
                className="w-full rounded-lg bg-surface border border-border p-3 text-white outline-none focus:border-primary min-h-[120px]"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Explain the context and intent"
              />
            </div>

            <div className="pt-2">
              <Button variant="primary" size="lg" disabled={submitting}>
                {submitting ? "Creating…" : "Create Proposal"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
