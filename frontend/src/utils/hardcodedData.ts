import type { Poll, PollOption, Comment, Vote } from '../types';

// Hardcoded poll data for testing
export const hardcodedPolls: Poll[] = [
  {
    id: 'hardcoded-1',
    title: 'Install protected bike lanes on Washington Avenue from downtown to university district',
    description: 'Add dedicated, protected bicycle lanes along Washington Avenue to improve cyclist safety and encourage active transportation between downtown and the university.',
    created_by: 'hardcoded-user-1',
    created_at: '2025-01-10T10:00:00Z',
    updated_at: '2025-01-10T10:00:00Z',
    is_active: true,
    end_date: '2025-02-15T00:00:00Z',
    decision_type: 'level_b',
    your_vote_status: {
      status: 'none',
      resolved_vote_path: []
    }
  },
  {
    id: 'hardcoded-2',
    title: 'Launch 18-month curbside composting pilot in four residential neighborhoods',
    description: 'Begin organic waste collection service in Downtown, Westside, Riverside, and Eastside neighborhoods to reduce landfill waste and create compost for city parks.',
    created_by: 'hardcoded-user-2',
    created_at: '2025-01-20T14:30:00Z',
    updated_at: '2025-01-20T14:30:00Z',
    is_active: false,
    end_date: '2025-03-01T00:00:00Z',
    decision_type: 'level_b',
    your_vote_status: {
      status: 'voted',
      resolved_vote_path: ['hardcoded-user-2']
    }
  },
  {
    id: 'hardcoded-3',
    title: 'Complete Streets Policy',
    description: 'Design and maintain streets to safely accommodate all users including pedestrians, cyclists, transit riders, and motorists of all ages and abilities.',
    created_by: 'hardcoded-user-3',
    created_at: '2025-01-05T09:15:00Z',
    updated_at: '2025-01-05T09:15:00Z',
    is_active: true,
    end_date: '2025-01-31T00:00:00Z',
    decision_type: 'level_a',
    direction_choice: 'Transportation Safety',
    your_vote_status: {
      status: 'delegated',
      resolved_vote_path: ['hardcoded-user-3', 'delegate-user-1'],
      final_delegatee_id: 'delegate-user-1'
    }
  },
  {
    id: 'hardcoded-4',
    title: 'Extend public library hours to 9 PM on weekdays for six-month trial',
    description: 'Extend operating hours at the main library to better serve students, working families, and evening library users.',
    created_by: 'hardcoded-user-4',
    created_at: '2025-01-15T11:20:00Z',
    updated_at: '2025-01-15T11:20:00Z',
    is_active: true,
    end_date: '2025-02-28T00:00:00Z',
    decision_type: 'level_b',
    your_vote_status: {
      status: 'none',
      resolved_vote_path: []
    }
  },
  {
    id: 'hardcoded-5',
    title: 'Public Records Transparency Policy',
    description: 'Make all public records and datasets available online unless specifically exempted by law, with clear processes for requesting information.',
    created_by: 'hardcoded-user-5',
    created_at: '2025-01-08T16:45:00Z',
    updated_at: '2025-01-08T16:45:00Z',
    is_active: true,
    end_date: '2025-02-10T00:00:00Z',
    decision_type: 'level_a',
    direction_choice: 'Government Transparency',
    your_vote_status: {
      status: 'voted',
      resolved_vote_path: ['hardcoded-user-5']
    }
  },
  {
    id: 'hardcoded-6',
    title: 'Plant 750 street trees along major transit corridors and in underserved neighborhoods',
    description: 'Add urban trees along bus routes and in neighborhoods with low tree canopy to improve air quality, provide shade, and enhance walkability.',
    created_by: 'hardcoded-user-6',
    created_at: '2025-01-12T13:30:00Z',
    updated_at: '2025-01-12T13:30:00Z',
    is_active: true,
    end_date: '2025-03-15T00:00:00Z',
    decision_type: 'level_b',
    your_vote_status: {
      status: 'none',
      resolved_vote_path: []
    }
  },
  {
    id: 'hardcoded-7',
    title: 'Green Building Standards for Municipal Construction',
    description: 'Require all new municipal buildings and major renovations to meet LEED Silver certification or equivalent energy efficiency standards.',
    created_by: 'hardcoded-user-7',
    created_at: '2025-01-03T08:00:00Z',
    updated_at: '2025-01-03T08:00:00Z',
    is_active: true,
    end_date: '2025-02-20T00:00:00Z',
    decision_type: 'level_a',
    direction_choice: 'Environmental Policy',
    your_vote_status: {
      status: 'voted',
      resolved_vote_path: ['hardcoded-user-7']
    }
  },
  {
    id: 'hardcoded-8',
    title: 'Inclusive Housing Development Policy',
    description: 'Ensure 20% of all new residential development includes affordable housing units or equivalent contributions to the housing trust fund.',
    created_by: 'hardcoded-user-8',
    created_at: '2025-01-07T14:20:00Z',
    updated_at: '2025-01-07T14:20:00Z',
    is_active: true,
    end_date: '2025-02-25T00:00:00Z',
    decision_type: 'level_a',
    direction_choice: 'Housing & Development',
    your_vote_status: {
      status: 'none',
      resolved_vote_path: []
    }
  }
];

// Hardcoded poll options for level_a polls
export const hardcodedPollOptions: Record<string, PollOption[]> = {
  'hardcoded-3': [
    {
      id: 'option-3a',
      poll_id: 'hardcoded-3',
      text: 'Prioritize pedestrian and cyclist safety in all street design decisions',
      created_at: '2025-01-05T09:15:00Z',
      updated_at: '2025-01-05T09:15:00Z'
    },
    {
      id: 'option-3b',
      poll_id: 'hardcoded-3',
      text: 'Maintain current street design standards with minor safety improvements',
      created_at: '2025-01-05T09:15:00Z',
      updated_at: '2025-01-05T09:15:00Z'
    }
  ],
  'hardcoded-5': [
    {
      id: 'option-5a',
      poll_id: 'hardcoded-5',
      text: 'Proactively publish all public records online with clear search and access tools',
      created_at: '2025-01-08T16:45:00Z',
      updated_at: '2025-01-08T16:45:00Z'
    },
    {
      id: 'option-5b',
      poll_id: 'hardcoded-5',
      text: 'Maintain current records system with improved request processing',
      created_at: '2025-01-08T16:45:00Z',
      updated_at: '2025-01-08T16:45:00Z'
    }
  ],
  'hardcoded-7': [
    {
      id: 'option-7a',
      poll_id: 'hardcoded-7',
      text: 'Require LEED Silver or equivalent for all new municipal construction',
      created_at: '2025-01-03T08:00:00Z',
      updated_at: '2025-01-03T08:00:00Z'
    },
    {
      id: 'option-7b',
      poll_id: 'hardcoded-7',
      text: 'Encourage but don\'t require green building standards',
      created_at: '2025-01-03T08:00:00Z',
      updated_at: '2025-01-03T08:00:00Z'
    }
  ],
  'hardcoded-8': [
    {
      id: 'option-8a',
      poll_id: 'hardcoded-8',
      text: 'Require 20% affordable housing in all new residential development',
      created_at: '2025-01-07T14:20:00Z',
      updated_at: '2025-01-07T14:20:00Z'
    },
    {
      id: 'option-8b',
      poll_id: 'hardcoded-8',
      text: 'Encourage affordable housing through incentives and partnerships',
      created_at: '2025-01-07T14:20:00Z',
      updated_at: '2025-01-07T14:20:00Z'
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

// Hardcoded comments/reasons for testing
export const hardcodedComments: Record<string, Comment[]> = {
  'hardcoded-3': [
    {
      id: 'comment-3a',
      poll_id: 'hardcoded-3',
      user: {
        id: 'hardcoded-user-1',
        username: 'alice'
      },
      body: 'Complete streets make our community more accessible for everyone, including seniors and people with disabilities. This is about equity and safety.',
      created_at: '2025-01-05T10:00:00Z',
      up_count: 12,
      down_count: 2,
      my_reaction: null
    },
    {
      id: 'comment-3b',
      poll_id: 'hardcoded-3',
      user: {
        id: 'hardcoded-user-2',
        username: 'bob'
      },
      body: 'I support this policy but we need to ensure it doesn\'t create traffic congestion. We should implement it gradually and monitor the impact.',
      created_at: '2025-01-05T11:30:00Z',
      up_count: 8,
      down_count: 1,
      my_reaction: null
    },
    {
      id: 'comment-3c',
      poll_id: 'hardcoded-3',
      user: {
        id: 'hardcoded-user-3',
        username: 'carol'
      },
      body: 'This aligns with our city\'s climate goals. More walking and cycling means fewer car trips and better air quality.',
      created_at: '2025-01-05T14:15:00Z',
      up_count: 15,
      down_count: 0,
      my_reaction: null
    }
  ],
  'hardcoded-5': [
    {
      id: 'comment-5a',
      poll_id: 'hardcoded-5',
      user: {
        id: 'hardcoded-user-4',
        username: 'david'
      },
      body: 'Transparency builds trust. When citizens can easily access public records, they can better understand and participate in government decisions.',
      created_at: '2025-01-08T16:45:00Z',
      up_count: 20,
      down_count: 1,
      my_reaction: null
    },
    {
      id: 'comment-5b',
      poll_id: 'hardcoded-5',
      user: {
        id: 'hardcoded-user-5',
        username: 'eve'
      },
      body: 'We need to balance transparency with privacy. Some records contain sensitive personal information that shouldn\'t be publicly accessible.',
      created_at: '2025-01-08T17:20:00Z',
      up_count: 6,
      down_count: 3,
      my_reaction: null
    }
  ],
  'hardcoded-7': [
    {
      id: 'comment-7a',
      poll_id: 'hardcoded-7',
      user: {
        id: 'hardcoded-user-6',
        username: 'frank'
      },
      body: 'LEED Silver certification is a reasonable standard that balances environmental benefits with cost considerations.',
      created_at: '2025-01-03T09:00:00Z',
      up_count: 11,
      down_count: 2,
      my_reaction: null
    }
  ]
};

export function getHardcodedComments(pollId: string): Comment[] {
  return hardcodedComments[pollId] || [];
}

// Hardcoded vote data for testing
export const hardcodedVotes: Record<string, Vote> = {
  'hardcoded-3': {
    id: 'vote-3',
    poll_id: 'hardcoded-3',
    option_id: 'option-3a',
    voter_id: 'hardcoded-user-current',
    created_at: '2025-01-05T10:00:00Z'
  },
  'hardcoded-5': {
    id: 'vote-5',
    poll_id: 'hardcoded-5',
    option_id: 'option-5a',
    voter_id: 'hardcoded-user-current',
    created_at: '2025-01-08T16:45:00Z'
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
