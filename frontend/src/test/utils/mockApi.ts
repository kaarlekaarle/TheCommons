import { vi } from 'vitest';
import type { User, DelegationInfo, CreateDelegationRequest, RemoveDelegationRequest } from '../../types';
import type { ContentResponse } from '../../types/content';

// Mock API response types
export interface MockApiResponse<T = any> {
  data: T;
  status?: number;
}

export interface MockApiError {
  response?: {
    status: number;
    data: { detail: string };
  };
  message: string;
}

// Mock user data
export const mockUsers: User[] = [
  {
    id: 'user-1',
    username: 'alice',
    email: 'alice@example.com',
    avatar_url: 'https://example.com/alice.jpg',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'user-2',
    username: 'bob',
    email: 'bob@example.com',
    avatar_url: 'https://example.com/bob.jpg',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z'
  },
  {
    id: 'user-3',
    username: 'charlie',
    email: 'charlie@example.com',
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z'
  }
];

// Mock delegation data
export const mockDelegationInfo: DelegationInfo = {
  global: {
    to_user_id: 'user-2',
    to_user_name: 'Bob',
    active: true,
    chain: [
      { user_id: 'user-1', user_name: 'Alice' },
      { user_id: 'user-2', user_name: 'Bob' }
    ]
  },
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

// Mock content data
export const mockContentResponse: ContentResponse = {
  principles: [
    {
      id: 'principle-1',
      title: 'Test Principle',
      description: 'A test principle',
      order: 1
    }
  ],
  actions: [
    {
      id: 'action-1',
      title: 'Test Action',
      description: 'A test action',
      principle_id: 'principle-1',
      order: 1
    }
  ],
  stories: [
    {
      id: 'story-1',
      title: 'Test Story',
      description: 'A test story',
      principle_id: 'principle-1',
      order: 1
    }
  ]
};

// Mock auth user data
export const mockAuthUser: User = {
  id: 'user-1',
  username: 'alice',
  email: 'alice@example.com',
  avatar_url: 'https://example.com/alice.jpg',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

// API Mock Helpers
export const createMockApi = () => {
  const mockApi = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
  };

  return mockApi;
};

// Delegation API Mocks
export const mockDelegationApi = {
  // Search users
  searchUsers: {
    success: (query: string = 'alice') => ({
      data: mockUsers.filter(user => 
        user.username.toLowerCase().includes(query.toLowerCase()) ||
        user.email.toLowerCase().includes(query.toLowerCase())
      )
    }),
    empty: () => ({ data: [] }),
    error: (status: number = 500, message: string = 'Server error') => ({
      response: { status, data: { detail: message } },
      message: 'Request failed'
    })
  },

  // Get my delegation
  getMyDelegation: {
    success: () => ({ data: mockDelegationInfo }),
    error: (status: number = 500, message: string = 'Internal server error') => ({
      response: { status, data: { detail: message } },
      message: 'Network error'
    })
  },

  // Create delegation
  createDelegation: {
    success: () => ({ data: {} }),
    error: (status: number = 400, message: string = 'Invalid delegation') => ({
      response: { status, data: { detail: message } },
      message: 'Request failed'
    })
  },

  // Remove delegation
  removeDelegation: {
    success: () => ({ data: {} }),
    error: (status: number = 404, message: string = 'Delegation not found') => ({
      response: { status, data: { detail: message } },
      message: 'Request failed'
    })
  }
};

// Content API Mocks
export const mockContentApi = {
  getContent: {
    success: () => ({ data: mockContentResponse }),
    error: (status: number = 500, message: string = 'Failed to fetch content') => ({
      response: { status, data: { detail: message } },
      message: 'Request failed'
    })
  }
};

// Auth API Mocks
export const mockAuthApi = {
  getMe: {
    success: () => ({ data: mockAuthUser }),
    error: (status: number = 401, message: string = 'Unauthorized') => ({
      response: { status, data: { detail: message } },
      message: 'Authentication failed'
    })
  },
  getProfile: {
    success: () => ({ data: mockAuthUser }),
    error: (status: number = 404, message: string = 'Profile not found') => ({
      response: { status, data: { detail: message } },
      message: 'Profile not found'
    })
  }
};

// Setup API mocks for tests
export const setupApiMocks = (mockApi: any) => {
  // Default to success responses
  mockApi.get.mockResolvedValue({ data: {} });
  mockApi.post.mockResolvedValue({ data: {} });
  mockApi.put.mockResolvedValue({ data: {} });
  mockApi.delete.mockResolvedValue({ data: {} });
  mockApi.patch.mockResolvedValue({ data: {} });

  return mockApi;
};

// Helper to mock specific API calls
export const mockApiCall = (
  mockApi: any,
  method: 'get' | 'post' | 'put' | 'delete' | 'patch',
  url: string,
  response: any
) => {
  mockApi[method].mockImplementation((callUrl: string) => {
    if (callUrl === url) {
      return Promise.resolve(response);
    }
    return Promise.resolve({ data: {} });
  });
};

// Helper to mock API errors
export const mockApiError = (
  mockApi: any,
  method: 'get' | 'post' | 'put' | 'delete' | 'patch',
  url: string,
  error: MockApiError
) => {
  mockApi[method].mockImplementation((callUrl: string) => {
    if (callUrl === url) {
      return Promise.reject(error);
    }
    return Promise.resolve({ data: {} });
  });
};

// Common error responses
export const commonErrors = {
  unauthorized: {
    response: { status: 401, data: { detail: 'Unauthorized' } },
    message: 'Authentication required'
  },
  forbidden: {
    response: { status: 403, data: { detail: 'Forbidden' } },
    message: 'Access denied'
  },
  notFound: {
    response: { status: 404, data: { detail: 'Not found' } },
    message: 'Resource not found'
  },
  rateLimited: {
    response: { status: 429, data: { detail: 'Rate limited' } },
    message: 'Too many requests'
  },
  serverError: {
    response: { status: 500, data: { detail: 'Internal server error' } },
    message: 'Server error'
  }
};
