import type { DelegationSummary, Delegation } from '../api/delegationsApi';
import type { Poll, User, Label } from '../types';

export const mockDelegationSummary: DelegationSummary = {
  ok: true,
  counts: { mine: 3, inbound: 5 },
  adoption: {
    commonsPct: 25,
    legacyPct: 75,
    transitions: 2
  },
  meta: {
    errors: [],
    trace_id: 'test-trace-123',
    generated_at: new Date().toISOString()
  }
};

export const mockDelegation: Delegation = {
  id: 'delegation-1',
  mode: 'FLEXIBLE_DOMAIN',
  fieldId: 'environment',
  personId: 'user-123',
  expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
};

export const mockUser: User = {
  id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  is_active: true
};

export const mockPoll: Poll = {
  id: 'poll-1',
  title: 'Test Poll',
  description: 'A test poll',
  decision_type: 'level_a',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  created_by: 'user-123',
  is_active: true,
  labels: []
};

export const mockLabel: Label = {
  id: 'label-1',
  name: 'Environment',
  slug: 'environment',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z'
};
