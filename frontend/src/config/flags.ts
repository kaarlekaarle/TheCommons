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
};

// Legacy export for backward compatibility
export const delegationEnabled = flags.delegationEnabled;
