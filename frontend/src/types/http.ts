// HTTP response types for API safety
export type Json = string | number | boolean | null | Json[] | { [k: string]: Json };

// Delegation-specific types
export interface DelegationGlobal {
  delegatee_username?: string;
  delegatee_id?: string;
  created_at?: string;
}

export interface DelegationPerLabel {
  label: {
    slug: string;
    name: string;
  };
  delegate: {
    username: string;
    id: string;
  };
  created_at?: string;
}
