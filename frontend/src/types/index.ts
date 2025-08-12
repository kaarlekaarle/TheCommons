// User types
export interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Poll/Proposal types
export interface VoteStatus {
  status: string; // 'delegated', 'voted', or 'none'
  resolved_vote_path: string[];
  final_delegatee_id?: string;
}

export interface Poll {
  id: string;
  title: string;
  description: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  end_date?: string;
  your_vote_status?: VoteStatus;
}

export interface PollOption {
  id: string;
  poll_id: string;
  text: string;
  created_at: string;
  updated_at: string;
}

export interface Vote {
  id: string;
  poll_id: string;
  option_id: string;
  voter_id: string;
  created_at: string;
}

export interface PollResults {
  poll_id: string;
  total_votes: number;
  options: Array<{
    option_id: string;
    text: string;
    votes: number;
    percentage: number;
  }>;
}

// Delegation types
export interface DelegationInfo {
  has_delegate: boolean;
  delegate_id?: string;
  delegate_username?: string;
  delegate_email?: string;
  created_at?: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  version: string;
  database: string;
  redis?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface ErrorResponse {
  detail: string;
  status_code?: number;
}

// Error types
export interface ApiError {
  status: number;
  message: string;
}

// Activity types
export interface ActivityUser {
  id: string;
  username: string;
}

export interface ActivityItem {
  type: 'proposal' | 'vote' | 'delegation';
  id: string;
  user: ActivityUser;
  timestamp: string;
  details: string;
}

// Comment types
export interface CommentUser {
  id: string;
  username: string;
}

export interface Comment {
  id: string;
  poll_id: string;
  user: CommentUser;
  body: string;
  created_at: string;
  up_count: number;
  down_count: number;
  my_reaction?: 'up' | 'down' | null;
}

export interface CommentList {
  comments: Comment[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// Reaction types
export interface ReactionResponse {
  up_count: number;
  down_count: number;
  my_reaction?: 'up' | 'down' | null;
}

export interface ReactionSummary {
  up_count: number;
  down_count: number;
}

// Axios error response
export interface AxiosErrorResponse {
  response?: {
    data?: {
      detail?: string;
    };
    status?: number;
  };
  message?: string;
}
