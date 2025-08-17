export interface DelegationChain {
  user_id: string;
  user_name?: string;
}

export interface GlobalDelegation {
  to_user_id: string;
  to_user_name?: string;
  active: boolean;
  chain: DelegationChain[];
}

export interface PollDelegation {
  poll_id: string;
  to_user_id: string;
  to_user_name?: string;
  active: boolean;
  chain: DelegationChain[];
}

export interface DelegationInfo {
  global?: GlobalDelegation;
  poll?: PollDelegation;
  created_at?: string;
  updated_at?: string;
}

export interface CreateDelegationRequest {
  to_user_id: string;
  scope: "global" | "poll";
  poll_id?: string;
}

export interface RemoveDelegationRequest {
  scope: "global" | "poll";
  poll_id?: string;
}

export interface DomainDelegation {
  domainId: string;
  domainName: string;
  target: { kind: 'person'; id: string; name: string };
  status: string[];
  expiresAt?: string;
  anonymity?: boolean;
}
