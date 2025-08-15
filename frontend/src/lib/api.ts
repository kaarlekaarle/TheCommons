import axios from 'axios';
import type { Poll, PollOption, Vote, PollResults, User, DelegationInfo, ActivityItem, CommentList, Comment, ReactionResponse, ReactionSummary, AxiosErrorResponse, DecisionType, Label, DelegationSummary, LabelOverview, PopularLabel } from '../types';
import type { DelegationInfo as NewDelegationInfo, CreateDelegationRequest, RemoveDelegationRequest } from '../types/delegation';
import type { PrincipleItem, ActionItem, StoryItem } from '../types/content';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    // Dispatch custom event for debug overlay
    window.dispatchEvent(new CustomEvent('api-call', {
      detail: {
        method: response.config.method?.toUpperCase() || 'GET',
        url: response.config.url || '',
        status: response.status,
      }
    }));
    return response;
  },
  (error) => {
    // Dispatch custom event for debug overlay (error case)
    window.dispatchEvent(new CustomEvent('api-call', {
      detail: {
        method: error.config?.method?.toUpperCase() || 'GET',
        url: error.config?.url || '',
        status: error.response?.status || 0,
      }
    }));

    if (error.response?.status === 401) {
      console.log('[AUTH DEBUG] 401 Unauthorized response - Removing token');
      localStorage.removeItem('token');
      // Don't reload the page automatically - let the component handle the error
      // This prevents the "Proposal not found" issue when tokens expire
    }
    return Promise.reject(error);
  }
);

// API Helper Functions
export const listPolls = async (params?: { decision_type?: DecisionType; label?: string; limit?: number; offset?: number }) => {
  try {
    console.log('API: Making request to /api/polls/');
    console.log('API: Token in localStorage:', !!localStorage.getItem('token'));
    console.log('API: Params:', params);

    const queryParams = new URLSearchParams();
    if (params?.decision_type) {
      queryParams.append('decision_type', params.decision_type);
    }
    if (params?.label) {
      queryParams.append('label', params.label);
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.offset) {
      queryParams.append('offset', params.offset.toString());
    }

    const url = queryParams.toString() ? `/api/polls/?${queryParams.toString()}` : '/api/polls/';
    const response = await api.get(url);
    console.log('API: Response received:', response.status, response.data.length, 'polls');
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    console.error('API: Error in listPolls:', err);
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch polls'
    };
  }
};

export const createProposal = async (pollData: {
  title: string;
  description: string;
  decision_type: "level_a" | "level_b";
  direction_choice?: string | null;
  labels?: string[];
}): Promise<Poll> => {
  try {
    const response = await api.post('/api/polls/', pollData);
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    console.error('API Error in createProposal:', err.response?.status, err.response?.data);
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to create proposal'
    };
  }
};

export const getPoll = async (id: string, signal?: AbortSignal): Promise<Poll> => {
  // Check if we should use hardcoded data
  const useHardcodedData = import.meta.env.VITE_USE_HARDCODED_DATA === 'true';

  if (useHardcodedData) {
    // Import hardcoded data utilities
    const { getHardcodedPoll, isHardcodedPoll } = await import('../utils/hardcodedData');

    if (isHardcodedPoll(id)) {
      const poll = getHardcodedPoll(id);
      if (poll) {
        return poll;
      }
    }

    // If not found in hardcoded data, throw error
    throw {
      status: 404,
      message: 'Poll not found in hardcoded data'
    };
  }

  try {
    const response = await api.get(`/api/polls/${id}`, { signal });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    console.error('API Error in getPoll:', err.response?.status, err.response?.data);
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch poll'
    };
  }
};

// Label API functions
export const listLabels = async (includeInactive: boolean = false, signal?: AbortSignal): Promise<Label[]> => {
  try {
    const queryParams = new URLSearchParams();
    if (includeInactive) {
      queryParams.append('include_inactive', '1');
    }

    const url = queryParams.toString() ? `/api/labels/?${queryParams.toString()}` : '/api/labels/';
    const response = await api.get(url, { signal });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch labels'
    };
  }
};

export const getLabel = async (id: string): Promise<Label> => {
  try {
    const response = await api.get(`/api/labels/${id}`);
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch label'
    };
  }
};

export const getLabelBySlug = async (slug: string): Promise<Label> => {
  try {
    const response = await api.get(`/api/labels/slug/${slug}`);
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch label'
    };
  }
};



export const getPollOptions = async (pollId: string, signal?: AbortSignal): Promise<PollOption[]> => {
  // Check if we should use hardcoded data
  const useHardcodedData = import.meta.env.VITE_USE_HARDCODED_DATA === 'true';

  if (useHardcodedData) {
    // Import hardcoded data utilities
    const { getHardcodedPollOptions, isHardcodedPoll } = await import('../utils/hardcodedData');

    if (isHardcodedPoll(pollId)) {
      const options = getHardcodedPollOptions(pollId);
      return options;
    }

    // If not found in hardcoded data, return empty array
    return [];
  }

  try {
    const response = await api.get(`/api/options/poll/${pollId}`, { signal });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch poll options'
    };
  }
};



export const createOption = async (pollId: string, text: string): Promise<PollOption> => {
  try {
    const response = await api.post('/api/options/', { poll_id: pollId, text });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to create option'
    };
  }
};

export const getMyVoteForPoll = async (pollId: string, signal?: AbortSignal): Promise<Vote | null> => {
  // Check if we should use hardcoded data
  const useHardcodedData = import.meta.env.VITE_USE_HARDCODED_DATA === 'true';

  if (useHardcodedData) {
    // Import hardcoded data utilities
    const { getHardcodedVote, isHardcodedPoll } = await import('../utils/hardcodedData');

    if (isHardcodedPoll(pollId)) {
      return getHardcodedVote(pollId);
    }

    return null;
  }

  try {
    const response = await api.get(`/api/votes/poll/${pollId}/my-vote`, { signal });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    // If it's a 404, the user hasn't voted yet - this is normal
    if (err.response?.status === 404) {
      console.log('[DEBUG] No vote found for poll', pollId, '- user has not voted yet');
      return null;
    }
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch vote'
    };
  }
};

export const castVote = async (pollId: string, optionId: string): Promise<Vote> => {
  // Check if we should use hardcoded data
  const useHardcodedData = import.meta.env.VITE_USE_HARDCODED_DATA === 'true';

  if (useHardcodedData) {
    // Import hardcoded data utilities
    const { createHardcodedVote, isHardcodedPoll } = await import('../utils/hardcodedData');

    if (isHardcodedPoll(pollId)) {
      return createHardcodedVote(pollId, optionId);
    }
  }

  try {
    const response = await api.post('/api/votes/', {
      poll_id: pollId,
      option_id: optionId
    });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to cast vote'
    };
  }
};

export const updateVote = async (voteId: string, optionId: string): Promise<Vote> => {
  try {
    const response = await api.put(`/api/votes/${voteId}`, {
      option_id: optionId
    });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to update vote'
    };
  }
};



export const getResults = async (pollId: string, signal?: AbortSignal): Promise<PollResults> => {
  // Check if we should use hardcoded data
  const useHardcodedData = import.meta.env.VITE_USE_HARDCODED_DATA === 'true';

  if (useHardcodedData) {
    // Import hardcoded data utilities
    const { getHardcodedResults, isHardcodedPoll } = await import('../utils/hardcodedData');

    if (isHardcodedPoll(pollId)) {
      const results = getHardcodedResults(pollId);
      if (results) {
        return results;
      }
    }
  }

  try {
    const response = await api.get(`/api/polls/${pollId}/results`, { signal });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch results'
    };
  }
};



// User search functions
export const searchUserByUsername = async (username: string): Promise<User> => {
  try {
    const response = await api.get(`/api/users/search/${username}`);
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to search user'
    };
  }
};

export const searchUsers = async (query: string): Promise<{ id: string; name: string }[]> => {
  try {
    const response = await api.get(`/api/users/search?query=${encodeURIComponent(query)}`);
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to search users'
    };
  }
};

// Delegation API functions
export const getMyDelegate = async (): Promise<DelegationInfo> => {
  try {
    const response = await api.get('/api/delegations/me');
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch delegation'
    };
  }
};

export const setDelegate = async (delegateId: string): Promise<DelegationInfo> => {
  try {
    const response = await api.post('/api/delegations/direct', { delegatee_id: delegateId });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to set delegate'
    };
  }
};

export const removeDelegate = async (): Promise<void> => {
  try {
    await api.delete('/api/delegations/');
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to remove delegate'
    };
  }
};

export const getDelegationSummary = async (): Promise<DelegationSummary> => {
  try {
    const response = await api.get('/api/delegations/me/summary');
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch delegation summary'
    };
  }
};

export const setDelegation = async (delegateId: string, labelSlug?: string): Promise<DelegationInfo> => {
  try {
    const payload: { delegatee_id: string; label_slug?: string } = { delegatee_id: delegateId };
    if (labelSlug) {
      payload.label_slug = labelSlug;
    }

    const response = await api.post('/api/delegations/', payload);
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to set delegation'
    };
  }
};

// Activity feed API
export const getActivityFeed = async (limit: number = 20): Promise<ActivityItem[]> => {
  try {
    const response = await api.get(`/api/activity/?limit=${limit}`);
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    const errorObj = {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch activity feed'
    };
    console.log('API Error:', errorObj);
    throw errorObj;
  }
};

// Comment API functions
export async function listComments(pollId: string, params?: { limit?: number; offset?: number; kind?: string }, signal?: AbortSignal): Promise<CommentList> {
  // Check if we should use hardcoded data
  const useHardcodedData = import.meta.env.VITE_USE_HARDCODED_DATA === 'true';

  if (useHardcodedData) {
    // Import hardcoded data utilities
    const { getHardcodedComments, isHardcodedPoll } = await import('../utils/hardcodedData');

    if (isHardcodedPoll(pollId)) {
      const comments = getHardcodedComments(pollId);
      const limit = params?.limit || 20;
      const offset = params?.offset || 0;
      const paginatedComments = comments.slice(offset, offset + limit);

      return {
        comments: paginatedComments,
        total: comments.length,
        limit,
        offset,
        has_more: offset + limit < comments.length
      };
    }

    // If not found in hardcoded data, return empty list
    return {
      comments: [],
      total: 0,
      limit: params?.limit || 20,
      offset: params?.offset || 0,
      has_more: false
    };
  }

  try {
    const queryParams = new URLSearchParams();
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.offset) {
      queryParams.append('offset', params.offset.toString());
    }
    if (params?.kind) {
      queryParams.append('kind', params.kind);
    }

    const url = queryParams.toString() ? `/api/polls/${pollId}/comments?${queryParams.toString()}` : `/api/polls/${pollId}/comments`;
    const response = await api.get(url, { signal });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch comments'
    };
  }
}

export async function createComment(pollId: string, input: { body: string; option_id?: string; kind?: string; stance?: 'main' | 'counter' | 'neutral'; perspective?: 'primary' | 'alternate' }): Promise<Comment> {
  // Check if we should use hardcoded data
  const useHardcodedData = import.meta.env.VITE_USE_HARDCODED_DATA === 'true';

  if (useHardcodedData) {
    // Import hardcoded data utilities
    const { isHardcodedPoll } = await import('../utils/hardcodedData');

    if (isHardcodedPoll(pollId)) {
      // Create a mock comment for hardcoded data
      const mockComment: Comment = {
        id: `comment-${Date.now()}`,
        poll_id: pollId,
        user: {
          id: 'hardcoded-user-current',
          username: 'current-user'
        },
        body: input.body,
        created_at: new Date().toISOString(),
        up_count: 0,
        down_count: 0,
        my_reaction: null,
        perspective: input.perspective
      };

      return mockComment;
    }
  }

  try {
    const response = await api.post(`/api/polls/${pollId}/comments`, input);
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to create comment'
    };
  }
}

export async function deleteComment(commentId: string): Promise<void> {
  try {
    await api.delete(`/api/comments/${commentId}`);
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to delete comment'
    };
  }
}

export async function setCommentReaction(commentId: string, type: 'up' | 'down'): Promise<ReactionResponse> {
  try {
    const response = await api.post(`/api/comments/${commentId}/reactions`, { type });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to set reaction'
    };
  }
}

// Delegation API functions
export async function getMyDelegation(signal?: AbortSignal): Promise<NewDelegationInfo> {
  try {
    const response = await api.get('/api/delegations/me', { signal });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch delegation info'
    };
  }
}

export async function createDelegation(payload: CreateDelegationRequest): Promise<void> {
  try {
    await api.post('/api/delegations/', payload);
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to create delegation'
    };
  }
}

export async function removeDelegation(payload: RemoveDelegationRequest): Promise<void> {
  try {
    await api.delete('/api/delegations/', { data: payload });
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to remove delegation'
    };
  }
}

// User API functions
export async function getCurrentUser(): Promise<User> {
  try {
    const response = await api.get('/api/users/me');
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch current user'
    };
  }
}

// Content API functions
export async function getContentPrinciples(): Promise<PrincipleItem[]> {
  try {
    const response = await api.get('/api/content/principles');
    return response.data.items;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    console.warn('Failed to fetch content principles:', err.message);
    return [];
  }
}

export async function getContentActions(): Promise<ActionItem[]> {
  try {
    const response = await api.get('/api/content/actions');
    return response.data.items;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    console.warn('Failed to fetch content actions:', err.message);
    return [];
  }
}

export async function getContentStories(): Promise<StoryItem[]> {
  try {
    const response = await api.get('/api/content/stories');
    return response.data.items;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    console.warn('Failed to fetch content stories:', err.message);
    return [];
  }
}

export async function getLabelOverview(
  slug: string,
  params?: {
    tab?: 'all' | 'principles' | 'actions';
    page?: number;
    per_page?: number;
    sort?: 'newest' | 'oldest';
  },
  signal?: AbortSignal
): Promise<LabelOverview> {
  try {
    const queryParams = new URLSearchParams();
    if (params?.tab) {
      queryParams.append('tab', params.tab);
    }
    if (params?.page) {
      queryParams.append('page', params.page.toString());
    }
    if (params?.per_page) {
      queryParams.append('per_page', params.per_page.toString());
    }
    if (params?.sort) {
      queryParams.append('sort', params.sort);
    }

    const url = queryParams.toString() ? `/api/labels/${slug}/overview?${queryParams.toString()}` : `/api/labels/${slug}/overview`;
    const response = await api.get(url, { signal });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch label overview'
    };
  }
}

export async function getPopularLabels(limit: number = 8, signal?: AbortSignal): Promise<PopularLabel[]> {
  try {
    const response = await api.get(`/api/labels/popular/public?limit=${limit}`, { signal });
    return response.data;
  } catch (error: unknown) {
    const err = error as AxiosErrorResponse;
    throw {
      status: err.response?.status || 500,
      message: err.response?.data?.detail || err.message || 'Failed to fetch popular labels'
    };
  }
}



export default api;
