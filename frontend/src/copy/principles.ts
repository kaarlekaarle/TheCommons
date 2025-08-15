export const principlesCopy = {
  // Main header
  mainQuestion: "What role do we want AI to play in education in the long run?",
  introText: "This page captures our community's current direction on the question, and an alternate perspective. People can propose revisions, add reasons, and learn more.",
  
  // Perspective sections
  primaryPerspective: {
    title: "Primary perspective",
    badge: "Current community view",
    summary: "We should use AI to extend great teaching, not replace it. That means human-led classrooms, AI as a supportive tool, and clear boundaries around safety, privacy, and fairness. Students learn best when curiosity and relationship stay at the center, and technology makes quality learning more personal, more accessible, and less unequal.",
    readMore: "Read more",
    readLess: "Hide",
    longBody: `In practice, AI helps teachers with planning, feedback, translation, accessibility, and differentiation, so they have more time for mentoring and discussion. Students can get immediate, scaffolded help that matches their level, with built-in guardrails that point them back to source material and reflective thinking instead of giving final answers.

Equity matters: AI should reduce gaps, not widen them. Publicly accountable tools and open resources prevent a pay-to-win system. Privacy is non-negotiable; student data should be minimal, protected, and never sold. Schools pilot before scaling, measure outcomes beyond test scores (well-being, engagement, belonging), and involve families and communities in oversight.

The long-term aim is human flourishing: better reading, writing, and reasoning; more creative projects; and honest safeguards against bias and hallucinations. Where AI helps teachers teach and students think, we use it. Where it dulls judgment or shortcuts learning, we don't.`,
    alignButton: "I lean this way"
  },
  
  alternatePerspective: {
    title: "Alternate perspective",
    summary: "We should move carefully and limit AI in classrooms until we have strong, proven guardrails. Core skills, human connection, and student privacy can't be an experiment. AI may help in narrow, well-defined tasks, but default use should wait for independent evidence that benefits outweigh the risks for all students.",
    readMore: "Read more",
    readLess: "Hide",
    longBody: `The worry isn't new tech—it's unintended consequences: dependency, reduced writing and memory, biased outputs, opaque systems, and data risks for minors. Schools already juggle crowded curricula and uneven access; adding AI too fast can widen gaps between well-resourced and under-resourced communities.

A safer approach: keep AI out of core assessment; allow small, opt-in pilots with independent evaluation; require open documentation of model limits; and mandate local control over student data. Teachers need time and training to judge where (or if) these tools help. Until evidence is clear, protect the basics—literacy, numeracy, attention, and shared civic life—by keeping the bar high for classroom adoption.`,
    alignButton: "I lean this way"
  },

  // Composer section
  composer: {
    title: "Take part in the conversation",
    placeholder: "Share your reasoning. What's your experience, what worked or failed, what do you worry about?",
    perspectiveLabel: "This note speaks to:",
    perspectiveOptions: {
      primary: "Primary perspective",
      alternate: "Alternate perspective"
    },
    submitButton: "Post reasoning",
    helperText: "Please avoid personal data. Clear, concrete stories help everyone learn."
  },

  // Alignment UI
  alignment: {
    currentBanner: "You currently lean:",
    changeLink: "Change"
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
