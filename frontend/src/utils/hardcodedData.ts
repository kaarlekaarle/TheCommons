import type { Poll, PollOption, Comment, Vote } from '../types';

// Hardcoded poll data for testing
export const hardcodedPolls: Poll[] = [
  {
    id: 'ai-edu-001',
    title: 'AI in Education: A Tool for Stronger Learning',
    description: 'Our community leans toward using AI to support teachers and students—freeing teachers from routine tasks, offering tailored explanations, and improving access—while keeping education human at its core.',
    longform_main: `We believe AI can become a helpful part of everyday learning when it strengthens—not replaces—the human side of education. Many of us see how it could free teachers from routine tasks so they have more time for teaching, mentoring, and care. Students could get clearer, more personal explanations matched to their level and pace, instead of one-size-fits-all work. AI might also help those who struggle with language, reading, or learning differences. At the heart of this view is a simple idea: teachers remain the guides and the glue; AI is a tool that helps them do their work better. We know this will take steady adjustment and oversight. We want guardrails for privacy, fairness, and safety. But moving in this direction feels right if it keeps classrooms human, opens doors for more students, and helps teachers focus on what only people can do.`,
    extra: {
      counter_body: `Others in the community urge us to slow down. They worry that an easy helper becomes a quiet crutch—that students will lean on AI instead of learning to think through problems and make mistakes that teach them. They fear classrooms becoming less personal, more screen-based, and that the craft of teaching is reduced to managing tools. They also point out the risk of deepening inequality: not every child has the same access to devices, internet, or support at home. And privacy remains unsettled—what happens to a child's data, forever? From this view, small, carefully measured steps come first. Schools should clearly prove benefits, put strong protections in place, and never let machines shape what education is meant to be: people learning from people.`,
      evidence: [
        {
          title: 'UNESCO: AI and Education — Guidance for Policy Makers (2023)',
          source: 'UNESCO',
          year: 2023,
          url: 'https://unesdoc.unesco.org/ark:/48223/pf0000382555'
        },
        {
          title: 'Holmes, Bialik & Fadel (2019): Artificial Intelligence in Education',
          source: 'Curriculum Redesign',
          year: 2019,
          url: 'https://curriculumredesign.org/our-work/artificial-intelligence-in-education/'
        },
        {
          title: 'OECD: AI in Education — Evidence, Opportunities, Risks',
          source: 'OECD',
          year: 2023,
          url: 'https://www.oecd.org/education/'
        },
        {
          title: 'Luckin (2021): Machine Learning and Human Intelligence',
          source: 'Routledge',
          year: 2021,
          url: 'https://www.routledge.com/Machine-Learning-and-Human-Intelligence/Luckin/p/book/9780367565429'
        }
      ]
    },
    created_by: 'hardcoded-user-1',
    created_at: '2025-08-01T12:00:00Z',
    updated_at: '2025-08-15T12:00:00Z',
    is_active: true,
    end_date: '2025-12-31T00:00:00Z',
    decision_type: 'level_a',
    direction_choice: 'AI in Education',
    your_vote_status: {
      status: 'voted',
      resolved_vote_path: ['hardcoded-user-1']
    }
  },
  {
    id: 'ai-edu-b-001',
    title: 'Pilot AI-Assisted Feedback in Grade 9 Writing',
    description: 'A small, time-boxed pilot where teachers use AI tools to provide formative, personalized writing feedback, with opt-in families and strict privacy rules.',
    created_by: 'hardcoded-user-2',
    created_at: '2025-08-01T12:00:00Z',
    updated_at: '2025-08-15T12:00:00Z',
    is_active: true,
    end_date: '2025-12-31T00:00:00Z',
    decision_type: 'level_b',
    your_vote_status: {
      status: 'none',
      resolved_vote_path: []
    }
  }
];

// Hardcoded poll options for level_a polls
export const hardcodedPollOptions: Record<string, PollOption[]> = {
  'ai-edu-001': [
    {
      id: 'option-ai-edu-1a',
      poll_id: 'ai-edu-001',
      text: 'Support AI in Education',
      created_at: '2025-08-01T12:00:00Z',
      updated_at: '2025-08-15T12:00:00Z'
    },
    {
      id: 'option-ai-edu-1b',
      poll_id: 'ai-edu-001',
      text: 'Proceed with Caution',
      created_at: '2025-08-01T12:00:00Z',
      updated_at: '2025-08-15T12:00:00Z'
    }
  ],
  'ai-edu-b-001': [
    {
      id: 'option-ai-edu-b-1a',
      poll_id: 'ai-edu-b-001',
      text: 'Approve',
      created_at: '2025-08-01T12:00:00Z',
      updated_at: '2025-08-15T12:00:00Z'
    },
    {
      id: 'option-ai-edu-b-1b',
      poll_id: 'ai-edu-b-001',
      text: 'Modify',
      created_at: '2025-08-01T12:00:00Z',
      updated_at: '2025-08-15T12:00:00Z'
    },
    {
      id: 'option-ai-edu-b-1c',
      poll_id: 'ai-edu-b-001',
      text: 'Reject',
      created_at: '2025-08-01T12:00:00Z',
      updated_at: '2025-08-15T12:00:00Z'
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
  'ai-edu-001': [
    {
      id: 'comment-ai-edu-1a',
      poll_id: 'ai-edu-001',
      user: {
        id: 'hardcoded-user-1',
        username: 'alice'
      },
      body: 'I support using AI to help teachers focus on what they do best - mentoring and personalized instruction.',
      created_at: '2025-08-01T12:30:00Z',
      up_count: 5,
      down_count: 0,
      my_reaction: null
    },
    {
      id: 'comment-ai-edu-1b',
      poll_id: 'ai-edu-001',
      user: {
        id: 'hardcoded-user-2',
        username: 'bob'
      },
      body: 'We need to be very careful about privacy and ensure equal access for all students.',
      created_at: '2025-08-01T13:00:00Z',
      up_count: 3,
      down_count: 1,
      my_reaction: null
    }
  ],
  'ai-edu-b-001': [
    {
      id: 'comment-ai-edu-b-1a',
      poll_id: 'ai-edu-b-001',
      user: {
        id: 'hardcoded-user-2',
        username: 'bob'
      },
      body: 'This pilot approach with strict privacy controls and teacher oversight seems like a good way to test the concept.',
      created_at: '2025-08-01T12:30:00Z',
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
  'ai-edu-001': {
    id: 'vote-ai-edu-1',
    poll_id: 'ai-edu-001',
    option_id: 'option-ai-edu-1a',
    voter_id: 'hardcoded-user-current',
    created_at: '2025-08-01T12:00:00Z'
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
