// Upgraded principle proposal content following the Complete Streets Policy structure
// Each principle follows: Title + Framing → The Question → Directions → Community Examples → Background

// Import the Complete Streets content from compass
import { completeStreetsCopy } from './compass';

export const openDataTransparencyCopy = {
  title: "Open Data & Transparency Policy",
  framing: "A foundational compass that guides government accountability and public trust.",

  questionHeading: "The Question",
  questionBody:
    "Should Riverbend publish all public datasets, decisions, and rationales openly by default, or maintain selective disclosure with controlled access to government information?\n\nThis choice will shape how transparent and accessible our government becomes, affecting public trust, civic engagement, innovation, and administrative efficiency.",

  dir1: {
    title: "Publish all public data and decisions openly by default",
    summary:
      "Choose this direction to align with maximum transparency and public access to government information.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Public trust: transparency builds confidence in government decisions and reduces suspicion of hidden agendas.",
      "Civic engagement: open data enables residents to understand and participate in community decisions.",
      "Innovation: public datasets fuel civic tech, research, and community-driven solutions.",
      "Accountability: public scrutiny improves decision quality and reduces potential for corruption.",
      "Efficiency: reduces FOIA requests and administrative overhead of managing access controls."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Privacy risks: sensitive information might be accidentally exposed or misused.",
      "Security concerns: open data could reveal vulnerabilities or sensitive operational details.",
      "Misinterpretation: complex data without context could lead to public confusion or misinformation.",
      "Resource burden: preparing and maintaining high-quality public datasets requires significant staff time."
    ],
  },

  dir2: {
    title: "Maintain selective disclosure with controlled access",
    summary:
      "Choose this direction to align with careful information management and controlled transparency.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Privacy protection: prevents accidental exposure of sensitive personal or business information.",
      "Security: maintains control over potentially sensitive operational and strategic information.",
      "Quality control: ensures data is properly vetted and contextualized before public release.",
      "Resource efficiency: focuses limited staff time on high-priority transparency requests.",
      "Strategic discretion: allows government to manage timing and messaging of sensitive decisions."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Trust deficit: selective disclosure fuels suspicion and reduces public confidence in government.",
      "Access barriers: controlled access creates obstacles for researchers, journalists, and civic groups.",
      "Innovation loss: limited data access reduces potential for community-driven solutions.",
      "Accountability gaps: reduced transparency makes it harder to hold officials accountable."
    ],
  },

  communityExamplesHeading: "Community Reasoning (examples)",
  communityExamples: [
    "Maria (journalist): \"Open data helps me investigate and report on important community issues. Without it, I can't do my job effectively.\"",
    "David (business owner): \"I need access to zoning and development data to make informed business decisions. Transparency helps everyone.\"",
    "Sarah (privacy advocate): \"We need to be careful about what we release. Personal information could be misused or lead to discrimination.\"",
    "James (civic tech developer): \"Open data lets me build tools that help residents understand their community better.\""
  ],

  backgroundHeading: "Background",
  backgroundSummary:
    "Open government policies balance transparency with privacy and security. While transparency builds trust and enables civic engagement, it requires careful management to protect sensitive information and ensure data quality.",
  backgroundReadMore: [
    "The open data movement began in the early 2000s and has been adopted by governments worldwide.",
    "Riverbend's transparency approach will influence: (1) public trust in government, (2) civic engagement levels, (3) innovation opportunities, (4) administrative efficiency."
  ]
};

export const visionZeroSafetyCopy = {
  title: "Vision Zero Safety Commitment",
  framing: "A safety-first compass that guides all transportation and infrastructure decisions.",

  questionHeading: "The Question",
  questionBody:
    "Should Riverbend commit to Vision Zero—designing all streets to prevent traffic fatalities and serious injuries—or maintain current safety standards with incremental improvements?\n\nThis choice will fundamentally shape our approach to transportation safety, affecting street design, speed limits, enforcement priorities, and the balance between safety and mobility.",

  dir1: {
    title: "Commit to Vision Zero: design streets to prevent all fatalities and serious injuries",
    summary:
      "Choose this direction to align with a safety-first approach that prioritizes human life above all other considerations.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Human life priority: no traffic fatality is acceptable; safety must come before convenience or speed.",
      "Proven effectiveness: cities with Vision Zero see significant reductions in traffic deaths and injuries.",
      "Equity: protects vulnerable road users including children, seniors, and people with disabilities.",
      "Long-term savings: prevents costly medical expenses, legal costs, and lost productivity from crashes.",
      "Community health: safer streets encourage walking and cycling, improving public health outcomes."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Implementation costs: comprehensive street redesigns require significant upfront investment.",
      "Traffic impacts: safety measures may slow traffic and increase congestion for motorists.",
      "Enforcement challenges: achieving zero fatalities requires strict enforcement that may be unpopular.",
      "Balancing act: focusing solely on safety may neglect other important transportation goals."
    ],
  },

  dir2: {
    title: "Maintain current safety standards with incremental improvements",
    summary:
      "Choose this direction to align with balanced improvements that consider safety alongside other community needs.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Practical approach: focuses on achievable safety improvements within existing constraints.",
      "Cost effectiveness: incremental changes provide safety benefits without major infrastructure costs.",
      "Balanced priorities: considers safety alongside mobility, economic, and community needs.",
      "Public acceptance: gradual changes are more likely to gain community support and compliance.",
      "Flexibility: allows for case-by-case decisions based on specific local conditions and needs."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Insufficient ambition: incremental improvements may not achieve meaningful safety gains.",
      "Continued fatalities: accepting some traffic deaths as inevitable is morally problematic.",
      "Missed opportunities: gradual approach may miss systemic changes needed for real safety improvement.",
      "Equity gaps: incremental approach may not address safety disparities in underserved areas."
    ],
  },

  communityExamplesHeading: "Community Reasoning (examples)",
  communityExamples: [
    "Lisa (parent): \"My kids walk to school every day. I need to know they're safe. Vision Zero isn't optional for families.\"",
    "Mike (delivery driver): \"I support safety, but we need to balance it with keeping goods moving. Traffic delays hurt business.\"",
    "Elena (senior): \"I'm afraid to cross busy streets. Vision Zero would make our community accessible for everyone.\"",
    "Tom (emergency responder): \"We need to consider how safety measures affect our response times. Every second counts.\""
  ],

  backgroundHeading: "Background",
  backgroundSummary:
    "Vision Zero originated in Sweden in 1997 and has been adopted by cities worldwide. It represents a fundamental shift from accepting traffic deaths as inevitable to treating them as preventable through better design and policy.",
  backgroundReadMore: [
    "Vision Zero cities typically see 20-40% reductions in traffic fatalities within 5-10 years.",
    "Riverbend's safety commitment will influence: (1) street design standards, (2) speed limit policies, (3) enforcement priorities, (4) transportation budgets."
  ]
};

export const climateEquityActionCopy = {
  title: "Climate Equity Action Plan",
  framing: "A climate justice compass that guides environmental and social policy decisions.",

  questionHeading: "The Question",
  questionBody:
    "Should Riverbend prioritize achieving net-zero emissions by 2040 while ensuring climate benefits reach all communities equitably, or focus on economic growth and gradual environmental improvements?\n\nThis choice will shape our approach to climate action, affecting energy policy, transportation, housing, and how we balance environmental goals with economic and social equity concerns.",

  dir1: {
    title: "Prioritize net-zero emissions by 2040 with equitable climate benefits",
    summary:
      "Choose this direction to align with urgent climate action that benefits all community members.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Climate urgency: immediate action is needed to prevent catastrophic climate impacts.",
      "Equity focus: ensures climate solutions benefit low-income and marginalized communities first.",
      "Health benefits: reduces air pollution and improves public health outcomes for all residents.",
      "Economic opportunity: positions Riverbend as a leader in the clean energy economy.",
      "Future-proofing: prepares community for climate impacts and energy transition."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Economic costs: rapid transition may be expensive and could impact local businesses and jobs.",
      "Implementation challenges: achieving net-zero by 2040 requires unprecedented coordination and resources.",
      "Equity concerns: climate policies may disproportionately burden low-income residents.",
      "Uncertainty: rapid changes may create economic and social disruption."
    ],
  },

  dir2: {
    title: "Focus on economic growth with gradual environmental improvements",
    summary:
      "Choose this direction to align with balanced development that considers economic and environmental needs.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Economic stability: prioritizes job creation and business growth to support community prosperity.",
      "Gradual transition: allows time for technology development and cost reduction.",
      "Community choice: respects individual and business decisions about energy and transportation.",
      "Proven approaches: builds on existing environmental programs and voluntary initiatives.",
      "Flexibility: adapts to changing economic conditions and technological developments."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Climate inaction: gradual approach may not achieve necessary emissions reductions in time.",
      "Missed opportunities: delays in climate action may increase long-term costs and risks.",
      "Equity gaps: gradual approach may not address environmental justice concerns.",
      "Competitive disadvantage: other communities may gain economic advantages from early climate action."
    ],
  },

  communityExamplesHeading: "Community Reasoning (examples)",
  communityExamples: [
    "Aisha (environmental justice): \"Low-income communities already bear the brunt of pollution. We need climate action that puts us first.\"",
    "Carlos (small business): \"I want to go green, but I need help with the upfront costs. Climate action should support local businesses.\"",
    "Jennifer (energy worker): \"We need to ensure the transition to clean energy doesn't leave workers behind.\"",
    "Marcus (homeowner): \"Solar panels and electric vehicles are expensive. Climate action needs to be affordable for everyone.\""
  ],

  backgroundHeading: "Background",
  backgroundSummary:
    "Climate equity recognizes that climate change disproportionately affects marginalized communities while climate solutions must benefit everyone. The transition to a clean energy economy presents both challenges and opportunities for community development.",
  backgroundReadMore: [
    "The 2040 net-zero target aligns with international climate goals and scientific recommendations.",
    "Riverbend's climate approach will influence: (1) energy policy and infrastructure, (2) transportation systems, (3) housing and development, (4) economic development strategy."
  ]
};

export const affordableHousingCopy = {
  title: "Affordable Housing Priority",
  framing: "A housing justice compass that guides development and community planning decisions.",

  questionHeading: "The Question",
  questionBody:
    "Should Riverbend prioritize ensuring all residents have access to safe, affordable housing through strong policies and investments, or focus on market-driven development with limited housing assistance?\n\nThis choice will shape our housing market, affecting development patterns, community diversity, economic opportunity, and the balance between housing affordability and property rights.",

  dir1: {
    title: "Prioritize strong affordable housing policies and investments",
    summary:
      "Choose this direction to align with housing as a fundamental right and community priority.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Housing security: ensures all residents have stable, affordable housing regardless of income.",
      "Community diversity: maintains economic and demographic diversity as the community grows.",
      "Economic stability: reduces housing cost burden, allowing residents to invest in other needs.",
      "Public health: stable housing improves health outcomes and reduces social service costs.",
      "Workforce retention: helps attract and retain workers across all income levels."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Market interference: strong housing policies may distort the housing market and reduce supply.",
      "Cost burden: affordable housing requirements may increase costs for other residents and developers.",
      "Property rights: mandatory affordable housing may infringe on property owner rights.",
      "Implementation complexity: housing policies require significant administrative oversight and resources."
    ],
  },

  dir2: {
    title: "Focus on market-driven development with limited housing assistance",
    summary:
      "Choose this direction to align with market-based solutions and limited government intervention.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Market efficiency: allows housing supply to respond to demand without government distortion.",
      "Property rights: respects individual property owners' rights to develop and use their land.",
      "Cost effectiveness: relies on private investment rather than public subsidies.",
      "Flexibility: adapts to changing market conditions and community preferences.",
      "Voluntary approach: encourages voluntary affordable housing through incentives rather than mandates."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Market failure: housing markets often fail to provide affordable options for low-income residents.",
      "Gentrification: market-driven development may displace existing residents and reduce diversity.",
      "Housing insecurity: limited assistance may leave vulnerable residents without stable housing.",
      "Economic inequality: housing cost burden may exacerbate income inequality and social problems."
    ],
  },

  communityExamplesHeading: "Community Reasoning (examples)",
  communityExamples: [
    "Rosa (rental property owner): \"I want to provide affordable housing, but I need to cover my costs. Policies should help, not hurt, small landlords.\"",
    "Kevin (first-time homebuyer): \"Housing prices keep rising faster than my income. I need help to stay in my community.\"",
    "Patricia (senior): \"I've lived here 30 years, but rising property taxes are forcing me to consider moving.\"",
    "Devon (developer): \"I can build affordable housing, but I need zoning changes and financial incentives to make it work.\""
  ],

  backgroundHeading: "Background",
  backgroundSummary:
    "Housing affordability challenges affect communities nationwide, with rising costs outpacing income growth. The balance between housing access and market dynamics requires careful policy consideration.",
  backgroundReadMore: [
    "Housing costs typically should not exceed 30% of household income to be considered affordable.",
    "Riverbend's housing approach will influence: (1) development patterns, (2) community diversity, (3) economic opportunity, (4) social services needs."
  ]
};

export const participatoryBudgetingCopy = {
  title: "Participatory Budgeting Program",
  framing: "A democratic compass that guides budget allocation and community investment decisions.",

  questionHeading: "The Question",
  questionBody:
    "Should Riverbend implement participatory budgeting—allowing residents to directly decide how to spend a portion of the city budget—or maintain traditional budget processes with limited public input?\n\nThis choice will fundamentally change how budget decisions are made, affecting community engagement, resource allocation, and the balance between direct democracy and representative governance.",

  dir1: {
    title: "Implement participatory budgeting with direct resident decision-making",
    summary:
      "Choose this direction to align with direct democracy and community-driven budget allocation.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Democratic engagement: gives residents real power over budget decisions that affect their lives.",
      "Community ownership: residents become more invested in and knowledgeable about city finances.",
      "Equity: ensures budget priorities reflect the actual needs of diverse community members.",
      "Transparency: makes budget processes more visible and accessible to all residents.",
      "Innovation: community input often identifies creative solutions officials might miss."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Complexity: budget decisions require technical expertise that residents may lack.",
      "Participation gaps: may favor residents with more time and resources to participate.",
      "Fragmentation: community-driven projects may lack citywide coordination and planning.",
      "Administrative burden: participatory processes require significant staff time and resources."
    ],
  },

  dir2: {
    title: "Maintain traditional budget processes with limited public input",
    summary:
      "Choose this direction to align with expert-driven budget planning and administrative efficiency.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Expertise: budget decisions benefit from professional financial and planning expertise.",
      "Efficiency: streamlined processes avoid the complexity and time costs of broad participation.",
      "Coordination: centralized planning ensures projects align with citywide strategic goals.",
      "Accountability: elected officials remain directly responsible for budget decisions.",
      "Stability: traditional processes provide predictable budget cycles and planning."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Democratic deficit: excludes residents from decisions that directly affect their communities.",
      "Representation gaps: traditional processes may not reflect the priorities of all residents.",
      "Transparency issues: budget decisions may appear opaque and disconnected from community needs.",
      "Engagement decline: limited participation opportunities may reduce civic engagement over time."
    ],
  },

  communityExamplesHeading: "Community Reasoning (examples)",
  communityExamples: [
    "Sofia (community organizer): \"Participatory budgeting gives power back to the people. We know what our neighborhoods need better than anyone.\"",
    "Robert (business owner): \"I support community input, but budget decisions need financial expertise. We can't let popularity override fiscal responsibility.\"",
    "Maria (parent): \"I want a say in how our tax dollars are spent, especially on things that affect my kids like parks and schools.\"",
    "David (city employee): \"Participatory budgeting sounds good, but it requires a lot of staff time to implement properly.\""
  ],

  backgroundHeading: "Background",
  backgroundSummary:
    "Participatory budgeting originated in Porto Alegre, Brazil in 1989 and has been adopted by cities worldwide. It represents a shift from representative to direct democracy in budget allocation.",
  backgroundReadMore: [
    "Participatory budgeting typically allocates 1-15% of the city budget to community decision-making.",
    "Riverbend's budget approach will influence: (1) community engagement levels, (2) budget transparency, (3) resource allocation patterns, (4) civic participation."
  ]
};

export const digitalInclusionCopy = {
  title: "Digital Inclusion & Access",
  framing: "A technology equity compass that guides digital infrastructure and access decisions.",

  questionHeading: "The Question",
  questionBody:
    "Should Riverbend prioritize universal digital access—ensuring all residents have high-speed internet, digital literacy training, and technology resources—or focus on market-driven digital development with limited public intervention?\n\nThis choice will shape our digital infrastructure, affecting educational opportunities, economic access, social connectivity, and the digital divide between different communities.",

  dir1: {
    title: "Prioritize universal digital access and digital literacy",
    summary:
      "Choose this direction to align with digital equity and universal technology access.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Digital equity: ensures all residents can participate in the digital economy and society.",
      "Educational access: provides students and families with essential learning tools and resources.",
      "Economic opportunity: enables residents to access jobs, services, and entrepreneurial opportunities.",
      "Social inclusion: connects residents to community resources, services, and social networks.",
      "Future readiness: prepares the community for increasingly digital civic and economic life."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Cost burden: universal access programs require significant public investment and ongoing subsidies.",
      "Market interference: public programs may compete with or discourage private sector investment.",
      "Technology obsolescence: rapid technological change may make public investments quickly outdated.",
      "Implementation complexity: digital inclusion requires coordination across multiple sectors and stakeholders."
    ],
  },

  dir2: {
    title: "Focus on market-driven digital development with limited intervention",
    summary:
      "Choose this direction to align with private sector innovation and limited government involvement.",
    readMoreHeading: "Why choose this direction?",
    rationale: [
      "Market efficiency: allows private providers to respond to demand and innovate based on market signals.",
      "Cost effectiveness: relies on private investment rather than public subsidies.",
      "Innovation: private sector competition drives technological advancement and service improvements.",
      "Flexibility: market-driven approach adapts quickly to changing technology and consumer preferences.",
      "Fiscal responsibility: avoids large public investments in rapidly evolving technology."
    ],
    counterHeading: "Counterarguments (raised by the other direction)",
    counters: [
      "Digital divide: market-driven approach may leave low-income and rural areas underserved.",
      "Access gaps: private providers may not serve areas with low profit potential.",
      "Equity concerns: digital access becomes dependent on ability to pay, creating economic barriers.",
      "Social costs: lack of digital access may limit educational and economic opportunities for vulnerable populations."
    ],
  },

  communityExamplesHeading: "Community Reasoning (examples)",
  communityExamples: [
    "Jasmine (student): \"I need reliable internet for homework and college applications. Digital access shouldn't depend on where you live or how much money you have.\"",
    "Carlos (small business): \"High-speed internet is essential for my business. But I worry about the cost of public programs and their impact on my taxes.\"",
    "Sarah (senior): \"I want to stay connected with my family and access services online, but I need help learning how to use technology safely.\"",
    "Mike (tech worker): \"The private sector is already investing in digital infrastructure. Government programs might slow down innovation.\""
  ],

  backgroundHeading: "Background",
  backgroundSummary:
    "Digital inclusion recognizes that internet access and digital literacy are essential for full participation in modern society. The digital divide affects education, employment, healthcare, and civic engagement.",
  backgroundReadMore: [
    "The Federal Communications Commission defines broadband as 25 Mbps download and 3 Mbps upload speeds.",
    "Riverbend's digital approach will influence: (1) educational opportunities, (2) economic development, (3) social connectivity, (4) civic engagement."
  ]
};

// Export all principle copies for easy access
// These IDs map to actual poll IDs in the database
export const principleCopies = {
  // Open Data & Transparency - matches "Open Government Policy" and "Open Data & Transparency Charter"
  "15e377dd-009f-4b63-8911-dd3262f6c497": openDataTransparencyCopy, // Open Government Policy
  "50849879-7009-4e88-a1cc-e9d5499d834a": openDataTransparencyCopy, // Open Data & Transparency Charter

  // Vision Zero Safety - matches "Vision Zero Commitment"
  "ecc9eef8-03cf-42d6-8c0c-f3c093d48c61": visionZeroSafetyCopy, // Vision Zero Commitment
  "1171540f-cc68-49a6-a358-cb3f17127ad0": visionZeroSafetyCopy, // Vision Zero Commitment
  "4c2e2953-082b-486c-9d75-701ba57cb234": visionZeroSafetyCopy, // Vision Zero Commitment

  // Climate Equity Action - matches "Climate Action Framework"
  "f60cfc96-f5cd-4458-9ea9-9cdad2f4539c": climateEquityActionCopy, // Climate Action Framework
  "23281599-199a-464e-b9b2-6ffa73dad333": climateEquityActionCopy, // Climate Action Framework
  "e2e76f60-be76-4d24-bced-39f4a5c321dc": climateEquityActionCopy, // Climate Action Framework

  // Affordable Housing Priority - matches "Affordable Housing Priority"
  "2d0b94f7-2f41-42db-9916-4be5ebb4a7e2": affordableHousingCopy, // Affordable Housing Priority
  "f6f55dc6-40ab-4239-b812-bafeed6a3eaf": affordableHousingCopy, // Affordable Housing Priority
  "c73e5c88-c9a5-4709-adde-a8c972ca2ba0": affordableHousingCopy, // Affordable Housing Priority

  // Digital Inclusion - matches "Digital Inclusion"
  "5ea5d672-11de-4fd7-bfd0-1ff1044618fd": digitalInclusionCopy, // Digital Inclusion
  "6ee0c61a-949d-49e0-9bd2-feeba8462b85": digitalInclusionCopy, // Digital Inclusion
  "e4e6ad08-acc6-4609-a1aa-22f2ef010db8": digitalInclusionCopy, // Digital Inclusion

  // Test/Mock IDs for development and testing
  // Note: These map to the actual hardcoded poll titles
  "hardcoded-3": completeStreetsCopy, // "Complete Streets Policy"
  "hardcoded-5": openDataTransparencyCopy, // "Public Records Transparency Policy"
  "hardcoded-7": climateEquityActionCopy, // "Green Building Standards for Municipal Construction"
  "hardcoded-8": affordableHousingCopy, // "Inclusive Housing Development Policy"

  // Note: Participatory Budgeting doesn't have a direct match in the current database
  // We'll keep the original ID for future use
  "p-participatory-budgeting": participatoryBudgetingCopy,
};
