export const delegationCopy = {
  delegates_global: "You delegate globally to {name}.",
  delegates_poll: "You delegate this poll to {name}.",
  votes_self: "You currently vote for yourself.",
  chain_label: "Chain: {chain}",
  manage_link: "Manage…",
  loading: "Checking delegation…",
  error_loading: "Couldn't load delegation. Try again.",
  
  // Manager modal
  manager_title: "Manage Delegation",
  current_status: "Current Status",
  create_new: "Create New Delegation",
  search_placeholder: "Search for a user...",
  search_results_placeholder: "Search results would appear here...",
  delegate_to: "Delegate to {name}",
  creating: "Creating...",
  remove_delegation: "Remove Delegation",
  
  // New comprehensive modal
  manage_title: "Manage Delegation",
  scope_poll: "This poll only",
  scope_global: "Global",
  search_placeholder_new: "Search people…",
  delegate_cta: "Delegate",
  revoke_cta: "Revoke delegation",
  revoking: "Revoking…",
  delegating: "Delegating…",
  error_generic: "Something went wrong. Please try again.",
  helper_text: "Delegation lets you trust someone else to vote on your behalf. You can always change or revoke this later.",
  no_results: "No users found",
  self_delegation_hint: "You can't delegate to yourself.",
  
  // Compact status
  compact_delegating: "Delegating to {name}",
  compact_delegating_chain: "Delegating to {name} • {depth}-hop chain",
  compact_no_delegation: "No delegation",
  compact_loading: "Loading…",
  
  // Poll banner
  poll_banner_title: "You are delegating this poll to {name}",
  poll_banner_subtitle: "You can vote yourself or change your delegation.",
  
  // Onboarding
  onboarding_title: "Trust someone to vote for you",
  onboarding_body: "If you're busy or unsure, you can delegate your vote to someone you trust. You're always in control.",
  onboarding_got_it: "Got it",
  onboarding_learn_more: "Learn more",
} as const;
