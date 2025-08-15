export const principlesCopy = {
  // Main header
  mainQuestion: "What role do we want AI to play in education in the long run?",
  introText: "This page captures our community's current direction on the question, and an alternate perspective. People can propose revisions, add reasons, and learn more.",
  
  // Perspective sections
  primaryPerspective: {
    title: "Where most people lean (for now)",
    badge: "Current community view",
    summary: "We think AI should make classrooms more human, not less. It should free teachers from busywork, help students get more personal attention, and stay inside clear boundaries for safety, privacy, and fairness. Curiosity, trust, and relationships come first. Used this way, AI can support great teaching and make learning feel more personal and more fair.",
    readMore: "Read more",
    readLess: "Hide",
    longBody: `In practice, AI helps teachers with planning, feedback, translation, accessibility, and differentiation, so they have more time for mentoring and discussion. Students can get immediate, scaffolded help that matches their level, with built-in guardrails that point them back to source material and reflective thinking instead of giving final answers.

Equity matters: AI should reduce gaps, not widen them. Publicly accountable tools and open resources prevent a pay-to-win system. Privacy is non-negotiable; student data should be minimal, protected, and never sold. Schools pilot before scaling, measure outcomes beyond test scores (well-being, engagement, belonging), and involve families and communities in oversight.

The long-term aim is human flourishing: better reading, writing, and reasoning; more creative projects; and honest safeguards against bias and hallucinations. Where AI helps teachers teach and students think, we use it. Where it dulls judgment or shortcuts learning, we don't.`,
    alignButton: "This speaks to me"
  },
  
  alternatePerspective: {
    title: "Another way people answer this",
    summary: "Others say we should be cautious. Core skills, human connection, and student privacy come before any new tool. AI might fit in small, well-defined tasks, but the default should be to wait for strong, independent evidence that benefits outweigh the risks—for every student, not just some.",
    readMore: "Read more",
    readLess: "Hide",
    longBody: `The worry isn't new tech—it's unintended consequences: dependency, reduced writing and memory, biased outputs, opaque systems, and data risks for minors. Schools already juggle crowded curricula and uneven access; adding AI too fast can widen gaps between well-resourced and under-resourced communities.

A safer approach: keep AI out of core assessment; allow small, opt-in pilots with independent evaluation; require open documentation of model limits; and mandate local control over student data. Teachers need time and training to judge where (or if) these tools help. Until evidence is clear, protect the basics—literacy, numeracy, attention, and shared civic life—by keeping the bar high for classroom adoption.`,
    alignButton: "This speaks to me"
  },

  // Composer section
  composer: {
    title: "Add your note",
    placeholder: "Share a short story, concern, or idea that could help improve the text.",
    perspectiveLabel: "This note responds to:",
    perspectiveOptions: {
      primary: "Where most people lean",
      alternate: "Another way people answer"
    },
    submitButton: "Post note",
    helperText: "Please avoid personal data. Clear, concrete stories help everyone learn."
  },

  // Alignment UI
  alignment: {
    currentBanner: "You currently lean:",
    changeLink: "Change"
  },

  // Meta section
  meta: {
    lastUpdated: "Last updated",
    currentLeaning: "Current leaning",
    change7Days: "Change (7 days)"
  },

  // Conversation section
  conversation: {
    header: "Recent notes from the community"
  },

  // Further learning section
  furtherLearning: {
    title: "Further learning",
    subtitle: "Independent research, reviews, and guidance you can read to go deeper.",
    sources: [
      {
        title: "OECD: AI in Education—Promises and Pitfalls",
        description: "Overview of evidence and policy considerations for AI adoption in K-12 and higher ed.",
        url: "https://example.org/oecd-ai-edu"
      },
      {
        title: "UNESCO Guidance for Generative AI in Education",
        description: "Global principles on safety, inclusion, teacher roles, and data protection.",
        url: "https://example.org/unesco-ai-guidance"
      },
      {
        title: "Education Endowment Foundation: Evidence on Feedback & Tutoring",
        description: "What works for feedback and tutoring—and how AI might fit or fail.",
        url: "https://example.org/eef-feedback-tutoring"
      },
      {
        title: "Data & Privacy Best Practices for Schools",
        description: "Plain-language checklists for data minimization, consent, and vendor risk.",
        url: "https://example.org/privacy-best-practices"
      }
    ]
  },

  // Legacy support (keep for backward compatibility)
  headerTag: 'Principle',
  lastUpdated: 'Last updated',
  share: 'Share',
  created: 'Created',
  updated: 'Updated',
  labels: 'Labels',
  noLabels: 'No labels',
  retry: 'Retry',
  loading: 'Loading...',
  error: 'Error loading content',
  revisionPosted: 'Revision posted successfully',
  revisionError: 'Failed to post revision',
};
