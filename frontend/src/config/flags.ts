// Feature flags for The Commons
export const flags = {
  delegationEnabled:
    import.meta.env.MODE === 'development'
      ? true
      : (import.meta.env.VITE_DELEGATION_ENABLED === 'true'),

  delegationBetaAllowlist:
    (import.meta.env.VITE_DELEGATION_BETA_ALLOWLIST ?? '')
      .split(',')
      .map((s: string) => s.trim())
      .filter(Boolean),

  useDemoContent: import.meta.env.VITE_USE_DEMO_CONTENT === 'true',

  labelsEnabled:
    import.meta.env.MODE === 'development'
      ? true
      : (import.meta.env.VITE_LABELS_ENABLED === 'true'),

  allowPublicLabels: import.meta.env.VITE_ALLOW_PUBLIC_LABELS === 'true',

  compassEnabled: import.meta.env.VITE_COMPASS_ENABLED === 'true',
  principlesDocMode: import.meta.env.VITE_PRINCIPLES_DOC_MODE === 'true',
  principlesDocEnabled: import.meta.env.VITE_PRINCIPLES_DOC_ENABLED === 'true',
  primaryPerspectiveEnabled: import.meta.env.VITE_PRIMARY_PERSPECTIVE_ENABLED === 'true',
};

// Legacy export for backward compatibility
export const delegationEnabled = flags.delegationEnabled;
