import React, { useState, useEffect } from "react";
import Button from "../components/ui/Button";
import { createProposal } from "../lib/api";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Compass, Target } from "lucide-react";
import { LEVEL_A_CHOICES } from "../config/levelA";
import type { Label } from "../types";
import LabelSelector from "../components/ui/LabelSelector";
import { flags } from "../config/flags";
import { getProposalHrefById } from "../utils/navigation";

// Feature flag for Level A decisions
const LEVEL_A_ENABLED = import.meta.env.VITE_LEVEL_A_ENABLED !== "false";

export default function ProposalNew() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const [decisionType, setDecisionType] = useState<"level_a" | "level_b">("level_b");
  const [directionChoice, setDirectionChoice] = useState<string>("");
  const [selectedLabels, setSelectedLabels] = useState<Label[]>([]);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle type query parameter for preselection
  useEffect(() => {
    const typeParam = searchParams.get('type');
    if (typeParam === 'level_a' || typeParam === 'level_b') {
      setDecisionType(typeParam);
    }
  }, [searchParams]);

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
        labels: selectedLabels.map(label => label.slug),
      };
      const created = await createProposal(payload);
      navigate(getProposalHrefById(created.id, decisionType));
    } catch (err: unknown) {
      const error = err as { message?: string; response?: { data?: { message?: string } } };
      setError(error?.message || error?.response?.data?.message || "Could not create proposal.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="card">
        <div className="card-content space-y-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold text-gov-primary">Start a Proposal</h1>
            <p className="text-gov-text-muted mt-2 text-base">
              Choose what type of decision this is, then describe it clearly.
            </p>
          </div>

          {error && (
            <div className="border border-gov-danger bg-red-50 text-gov-danger rounded-lg p-3">
              {error}
            </div>
          )}

          {/* Decision Type Selector */}
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-gov-primary mb-2">What type of decision are you making?</h3>
              <p className="text-sm text-gov-text-muted">
                This helps the community understand the scope and impact of your proposal.
              </p>
            </div>

            <div className={`grid gap-4 ${LEVEL_A_ENABLED ? 'md:grid-cols-2' : 'md:grid-cols-1'}`}>
              {LEVEL_A_ENABLED && (
                <button
                  type="button"
                  onClick={() => setDecisionType("level_a")}
                  className={`rounded-xl border p-6 text-left transition-all duration-200 ${
                    decisionType === "level_a"
                      ? "border-gov-primary bg-blue-50 shadow-gov-md"
                      : "border-gov-border hover:border-gov-primary/40 hover:bg-blue-50/50"
                  }`}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      decisionType === "level_a" ? "bg-gov-primary" : "bg-gov-primary/10"
                    }`}>
                      <Compass className={`w-4 h-4 ${decisionType === "level_a" ? "text-white" : "text-gov-primary"}`} />
                    </div>
                    <div>
                      <div className="font-semibold text-gov-primary">Long-Term Direction</div>
                      <div className="text-xs text-gov-text-muted font-medium">Principle</div>
                    </div>
                  </div>
                  <div className="text-sm text-gov-text leading-relaxed">
                    A foundational value or principle that will guide many future decisions.
                    Sets the compass for the community.
                  </div>
                </button>
              )}

              <button
                type="button"
                onClick={() => setDecisionType("level_b")}
                className={`rounded-xl border p-6 text-left transition-all duration-200 ${
                  decisionType === "level_b"
                    ? "border-gov-secondary bg-yellow-50 shadow-gov-md"
                    : "border-gov-border hover:border-gov-secondary/40 hover:bg-yellow-50/50"
                }`}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    decisionType === "level_b" ? "bg-gov-secondary" : "bg-gov-secondary/10"
                  }`}>
                    <Target className={`w-4 h-4 ${decisionType === "level_b" ? "text-gov-primary" : "text-gov-secondary"}`} />
                  </div>
                  <div>
                    <div className="font-semibold text-gov-primary">Immediate Action</div>
                                          <div className="text-xs text-gov-text-muted">Action</div>
                  </div>
                </div>
                <div className="text-sm text-gov-text leading-relaxed">
                  A specific decision about what to do right now.
                  Can be adjusted as circumstances change.
                </div>
              </button>
            </div>
          </div>

          {/* Principle choices */}
          {decisionType === "level_a" && (
            <div className="space-y-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <Compass className="w-4 h-4 text-gov-primary" />
                <span className="text-gov-primary font-medium">Choose Your Community's Direction</span>
              </div>
              <p className="text-sm text-gov-text-muted mb-4">
                Select the value that will guide future decisions in this area.
              </p>
              <div className="space-y-3">
                {LEVEL_A_CHOICES.map((c) => (
                  <label key={c} className="flex items-center gap-3 p-4 rounded-lg border border-blue-200 hover:border-blue-300 cursor-pointer bg-white hover:bg-blue-50 transition-colors">
                    <input
                      type="radio"
                      name="direction_choice"
                      className="accent-gov-primary"
                      value={c}
                      checked={directionChoice === c}
                      onChange={() => setDirectionChoice(c)}
                    />
                    <span className="text-gov-text">{c}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Title/Description */}
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gov-text mb-1 font-medium">Title</label>
              <input
                className="w-full rounded-lg bg-white border border-gov-border p-3 text-gov-text outline-none focus:border-gov-primary focus:ring-2 focus:ring-gov-primary/20"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Give it a clear, short name"
              />
            </div>
            <div>
              <label className="block text-sm text-gov-text mb-1 font-medium">Description</label>
              <textarea
                className="w-full rounded-lg bg-white border border-gov-border p-3 text-gov-text outline-none focus:border-gov-primary focus:ring-2 focus:ring-gov-primary/20 min-h-[120px]"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Explain why it matters and what it will change"
              />
            </div>

            {/* Label selector */}
            {flags.labelsEnabled && (
              <LabelSelector
                selectedLabels={selectedLabels}
                onLabelsChange={setSelectedLabels}
                maxLabels={5}
                disabled={submitting}
              />
            )}

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
