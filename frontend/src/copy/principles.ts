// Placeholder principle content for The Commons MVP
// This demonstrates the structure for Level A principles

export const levelAPlaceholderCopy = {
  title: "Level A Principle (Placeholder)",
  framing: "A placeholder example for Level A principles.",

  questionHeading: "The Question",
  questionBody:
    "This is a placeholder example for Level A. It demonstrates how a single evolving document could be revised and countered.",

  dir1: {
    title: "Direction 1 (Placeholder)",
    summary: "This is a placeholder direction for demonstration purposes.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "This is a placeholder rationale point.",
      "This demonstrates how rationale points would be structured.",
      "This shows the format for Level A principle directions."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "This is a placeholder counterargument.",
      "This demonstrates how counterarguments would be structured.",
      "This shows the format for balanced discussion."
    ],
  },

  dir2: {
    title: "Direction 2 (Placeholder)",
    summary: "This is a placeholder direction for demonstration purposes.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "This is a placeholder rationale point.",
      "This demonstrates how rationale points would be structured.",
      "This shows the format for Level A principle directions."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "This is a placeholder counterargument.",
      "This demonstrates how counterarguments would be structured.",
      "This shows the format for balanced discussion."
    ],
  },

  communityExamplesHeading: "Community Reasoning (examples)",
  communityExamples: [
    "This is a placeholder community example.",
    "This demonstrates how community reasoning would be structured.",
    "This shows the format for community input."
  ],

  backgroundHeading: "Background",
  backgroundSummary:
    "This is a placeholder background summary for demonstration purposes.",
  backgroundReadMore: [
    "This is a placeholder background detail.",
    "This demonstrates how background information would be structured."
  ]
};

// Export all principle copies for easy access
// This maps to the placeholder principle ID
export const principleCopies = {
  "level-a-placeholder": levelAPlaceholderCopy,
  "hardcoded-1": levelAPlaceholderCopy,
};

// Debug logging to help identify issues
console.log('Principles copy loaded:', Object.keys(principleCopies));
