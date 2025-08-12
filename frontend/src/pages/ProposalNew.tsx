import React, { useState } from "react";
import Button from "../components/ui/Button";
import { createProposal } from "../lib/api";
import { useNavigate } from "react-router-dom";

const LEVEL_A_CHOICES = [
  "Environmental: Nature is for exploitation",
  "Environmental: Nature is to be cared for",
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
      return setError("Please pick a Level-A direction.");
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
      setError(err?.message || err?.response?.data?.message || "Could not create proposal.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="card">
        <div className="card-content space-y-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold">Start a Proposal</h1>
            <p className="text-muted mt-2">
              Choose what type of decision this is, then describe it clearly.
            </p>
          </div>

          {error && (
            <div className="border border-red-500/40 bg-red-500/10 text-red-300 rounded-lg p-3">
              {error}
            </div>
          )}

          {/* Decision Type Selector */}
          <div className="space-y-2">
            <label className="block text-sm text-muted">What type of decision is this?</label>
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
                  <div className="font-semibold">Principle (Level A)</div>
                  <div className="text-sm text-muted">
                    A long-term value or policy. Rarely changes.
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
                <div className="font-semibold">Action (Level B)</div>
                <div className="text-sm text-muted">
                  A concrete decision for now. Yes / No / Abstain.
                </div>
              </button>
            </div>
          </div>

          {/* Level A choices */}
          {decisionType === "level_a" && (
            <div className="space-y-3">
              <div className="text-sm text-muted">
                Choose the direction that best represents your community's values.
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
                placeholder="Give it a clear, short name"
              />
            </div>
            <div>
              <label className="block text-sm text-muted mb-1">Description</label>
              <textarea
                className="w-full rounded-lg bg-surface border border-border p-3 text-white outline-none focus:border-primary min-h-[120px]"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Explain why it matters and what it will change"
              />
            </div>

            <div className="pt-2">
              <Button type="submit" variant="primary" size="lg" disabled={submitting}>
                {submitting ? "Sharing…" : "Share"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
