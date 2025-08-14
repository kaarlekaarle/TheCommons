export const compassCopy = {
  // Main content
  framing: "A long-term compass that guides related community decisions.",
  directionsTitle: "Choose a direction to align with",
  reasoningTitle: "Take part in the conversation",
  conversationHeader: "Share your perspective",
  contextTitle: "Background",

  // Actions
  share: "Share",
  retry: "Try again",
  alignCta: "Align with this direction",
  postReasoning: "Post reasoning",
  posting: "Posting…",
  loadMore: "Load more",

  // Status messages
  alignedWith: "You're aligned with",
  changeAlignment: "Change alignment",
  alignedPill: "Aligned",
  alignedSubtext: "You can change your alignment any time.",
  postSuccess: "Reasoning posted.",

  // Section titles
  tallyTitle: "Community alignment (so far)",

  // Form labels
  reasoningLabel: "Share why you lean this way",
  reasoningHelper: "Short essay (240–1000 characters). Be concrete and constructive.",
  conversationPlaceholder: "Write your reasoning — what future does this lead to?",
  aboutLabel: "About",
  aboutGeneral: "General",
  toneLabel: "Tone",
  toneSupport: "Supporting",
  toneConcern: "Raising a concern",
  hintSupport: "This will be shown as support for this direction.",
  hintConcern: "This will be shown as a constructive concern for this direction.",

  // Empty states
  directionsEmpty: "Directions will appear here soon.",
  tallyEmpty: "No alignments yet.",
  conversationEmpty: "Be the first to share your reasoning.",

  // Error states
  errorTitle: "Compass unavailable",
  errorBody: "We couldn't load this compass right now.",
  directionsError: "Couldn't load directions.",
  tallyError: "Couldn't load alignment results.",
  conversationError: "Couldn't load community reasoning.",

  // Loading states
  loadingDirections: "Loading directions...",
  loadingTally: "Loading results...",
  loadingConversation: "Loading conversation...",
};

export const completeStreetsCopy = {
  title: "Complete Streets Policy",
  framing: "A long-term compass that guides related community decisions.",

  questionHeading: "The Question",
  questionBody:
    "Should Riverbend prioritize pedestrian and cyclist safety in all street design decisions, or maintain current street design standards with only minor safety improvements?\n\nThis choice will guide future transportation and land-use policies, affecting mobility, safety, equity, climate, and the local economy.",

  dir1: {
    title: "Prioritize pedestrian and cyclist safety in all street design decisions",
    summary:
      "Choose this direction to align with a safety-first, walkable and bike-friendly future.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Safety first: redesign to prevent fatalities and injuries, especially for vulnerable users.",
      "Equity & accessibility: benefits people without cars, including low-income residents, seniors, and people with disabilities.",
      "Climate goals: more walking, cycling, and transit reduce car dependence and emissions.",
      "Public health: active travel improves health and reduces air-pollution exposure.",
      "Economic vitality: walkable, bike-friendly areas attract business and raise street life."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Congestion risk: lane reductions/bike lanes can increase congestion in car-dependent areas.",
      "Business impact: shops reliant on drive-up customers and parking may lose footfall.",
      "Equity paradox: car-dependent suburban/rural residents may feel disadvantaged without transit alternatives.",
      "Cost & disruption: large redesigns are expensive and cause construction disruption."
    ],
  },

  dir2: {
    title: "Maintain current street design standards with minor safety improvements",
    summary:
      "Choose this direction to align with incremental change and minimizing disruption.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Practical improvements: targeted crosswalks, signals, and speed enforcement.",
      "Minimizing disruption: keeps traffic flowing for commuters, deliveries, and emergency services.",
      "Economic stability: protects businesses dependent on car access and parking.",
      "Cost efficiency: lower upfront costs than large-scale redesign.",
      "Flexibility: leaves room for gradual changes without a single radical shift."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Safety plateau: minor tweaks rarely deliver large crash/fatality reductions.",
      "Climate inaction: maintaining car dominance undermines emissions targets.",
      "Missed health benefits: fewer incentives for active travel.",
      "Long-term costs: short-term savings can mean higher future health, congestion, and environmental costs."
    ],
  },

  communityExamplesHeading: "Community Reasoning (examples)",
  communityExamples: [
    "Alice (equity): \"Complete streets make our community more accessible for everyone, including seniors and people with disabilities. This is about equity and safety.\"",
    "Bob (balanced): \"I support this, but we need to ensure it doesn't create traffic congestion. Let's implement gradually and monitor impacts.\"",
    "Carol (climate): \"This aligns with our city's climate goals. More walking and cycling means fewer car trips and better air quality.\"",
    "Dan (business): \"My shop depends on parking access. If we remove too many spaces, it could hurt local business.\""
  ],

  backgroundHeading: "Background",
  backgroundSummary:
    "'Complete Streets' designs streets for all users, not just cars. Research links redesigns to fewer injuries and deaths, but implementation can conflict with car-centric infrastructure, business needs, and commuter habits.",
  backgroundReadMore: [
    "The concept originated in the United States and has spread globally.",
    "Adopting a clear direction in Riverbend will shape: (1) transportation budgets, (2) zoning & development, (3) climate & health integration, (4) equity strategies."
  ]
};
