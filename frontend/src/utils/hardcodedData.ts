import type { Poll, PollOption, Comment, Vote } from '../types';

// Hardcoded poll data for testing
export const hardcodedPolls: Poll[] = [
  {
    id: 'hardcoded-1',
    title: 'Principle (Placeholder)',
    description: 'This is a placeholder example for principles. It demonstrates how a single evolving document could be revised and countered.',
    longform_main: `This is a comprehensive community document that outlines our approach to principles.

The document serves as a living, evolving guide that reflects the community's current understanding and consensus. It provides a foundation for decision-making while remaining open to revision and improvement.

Key aspects of this document include:
- Clear articulation of community values and priorities
- Framework for evaluating proposals and actions
- Mechanisms for ongoing review and refinement
- Integration with broader community goals

This document is not static but rather a dynamic expression of our collective wisdom, subject to continuous improvement through community input and deliberation.`,
    extra: {
      counter_body: `This counter-document presents an alternative perspective on the community's approach to principles.

While the main document emphasizes consensus and gradual evolution, this view suggests that more rapid and decisive changes may be necessary to address pressing community needs.

Key differences include:
- Faster decision-making processes
- Greater emphasis on immediate action over deliberation
- Different prioritization of community values
- Alternative frameworks for evaluation

This perspective acknowledges the value of the main document while offering a different path forward that may be more suitable for certain situations or community preferences.`,
      evidence: [
        {
          title: 'Vision Zero framework',
          source: 'WHO',
          year: 2023,
          url: 'https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries'
        },
        {
          title: 'Complete Streets economic impacts',
          source: 'RCTA',
          year: 2022,
          url: 'https://www.railstotrails.org/resource-library/resource/economic-benefits-of-complete-streets/'
        }
      ]
    },
    created_by: 'hardcoded-user-1',
    created_at: '2025-01-10T10:00:00Z',
    updated_at: '2025-01-10T10:00:00Z',
    is_active: true,
    end_date: '2025-02-15T00:00:00Z',
    decision_type: 'level_a',
    direction_choice: 'Placeholder',
    your_vote_status: {
      status: 'voted',
      resolved_vote_path: ['hardcoded-user-1']
    }
  },
  {
    id: 'hardcoded-2',
    title: 'Level B Principle (Placeholder)',
    description: 'This is a placeholder example for Level B. It demonstrates how community-level or technical sub-questions could be explored.',
    created_by: 'hardcoded-user-2',
    created_at: '2025-01-15T11:20:00Z',
    updated_at: '2025-01-15T11:20:00Z',
    is_active: true,
    end_date: '2025-02-28T00:00:00Z',
    decision_type: 'level_b',
    your_vote_status: {
      status: 'none',
      resolved_vote_path: []
    }
  }
];

// Hardcoded poll options for level_a polls
export const hardcodedPollOptions: Record<string, PollOption[]> = {
  'hardcoded-1': [
    {
      id: 'option-1a',
      poll_id: 'hardcoded-1',
      text: 'Direction 1 (Placeholder)',
      created_at: '2025-01-10T10:00:00Z',
      updated_at: '2025-01-10T10:00:00Z'
    },
    {
      id: 'option-1b',
      poll_id: 'hardcoded-1',
      text: 'Direction 2 (Placeholder)',
      created_at: '2025-01-10T10:00:00Z',
      updated_at: '2025-01-10T10:00:00Z'
    }
  ],
  'hardcoded-2': [
    {
      id: 'option-2a',
      poll_id: 'hardcoded-2',
      text: 'Approve',
      created_at: '2025-01-15T11:20:00Z',
      updated_at: '2025-01-15T11:20:00Z'
    },
    {
      id: 'option-2b',
      poll_id: 'hardcoded-2',
      text: 'Modify',
      created_at: '2025-01-15T11:20:00Z',
      updated_at: '2025-01-15T11:20:00Z'
    },
    {
      id: 'option-2c',
      poll_id: 'hardcoded-2',
      text: 'Reject',
      created_at: '2025-01-15T11:20:00Z',
      updated_at: '2025-01-15T11:20:00Z'
    }
  ]
};

// Utility functions for hardcoded data
export function getHardcodedPoll(id: string): Poll | null {
  return hardcodedPolls.find(poll => poll.id === id) || null;
}

export function getHardcodedPollOptions(pollId: string): PollOption[] {
  return hardcodedPollOptions[pollId] || [];
}

export function isHardcodedPoll(id: string): boolean {
  return hardcodedPolls.some(poll => poll.id === id);
}

// Hardcoded comments for testing
export const hardcodedComments: Record<string, Comment[]> = {
  'hardcoded-1': [
    {
      id: 'comment-1a',
      poll_id: 'hardcoded-1',
      user: {
        id: 'hardcoded-user-1',
        username: 'alice'
      },
      body: 'This is a placeholder comment for demonstration purposes.',
      created_at: '2025-01-10T10:30:00Z',
      up_count: 5,
      down_count: 0,
      my_reaction: null
    },
    {
      id: 'comment-1b',
      poll_id: 'hardcoded-1',
      user: {
        id: 'hardcoded-user-2',
        username: 'bob'
      },
      body: 'This demonstrates how comments would be structured.',
      created_at: '2025-01-10T11:00:00Z',
      up_count: 3,
      down_count: 1,
      my_reaction: null
    }
  ],
  'hardcoded-2': [
    {
      id: 'comment-2a',
      poll_id: 'hardcoded-2',
      user: {
        id: 'hardcoded-user-2',
        username: 'bob'
      },
      body: 'This is a placeholder comment for demonstration purposes.',
      created_at: '2025-01-15T11:30:00Z',
      up_count: 4,
      down_count: 0,
      my_reaction: null
    }
  ]
};

export function getHardcodedComments(pollId: string): Comment[] {
  return hardcodedComments[pollId] || [];
}

// Hardcoded vote data for testing
export const hardcodedVotes: Record<string, Vote> = {
  'hardcoded-1': {
    id: 'vote-1',
    poll_id: 'hardcoded-1',
    option_id: 'option-1a',
    voter_id: 'hardcoded-user-current',
    created_at: '2025-01-10T10:00:00Z'
  }
};

export function getHardcodedVote(pollId: string): Vote | null {
  return hardcodedVotes[pollId] || null;
}

export function createHardcodedVote(pollId: string, optionId: string): Vote {
  const vote: Vote = {
    id: `vote-${Date.now()}`,
    poll_id: pollId,
    option_id: optionId,
    voter_id: 'hardcoded-user-current',
    created_at: new Date().toISOString()
  };

  // Store the vote for future lookups
  hardcodedVotes[pollId] = vote;

  return vote;
}
