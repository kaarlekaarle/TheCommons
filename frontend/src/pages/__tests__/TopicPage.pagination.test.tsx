import { describe, it, expect } from 'vitest';
import type { PollSummary } from '../../types';

// Mock the merge and sort function used in TopicPage
function mergeAndSortPolls(existingItems: PollSummary[], newItems: PollSummary[]): PollSummary[] {
  // Use Map for idempotent merge
  const byId = new Map<string, PollSummary>();
  
  // Add existing items
  for (const poll of existingItems) {
    byId.set(String(poll.id), poll);
  }
  
  // Add/update with new items
  for (const poll of newItems) {
    byId.set(String(poll.id), poll);
  }
  
  const finalItems = Array.from(byId.values());
  
  // Stable sort by created_at DESC, then id DESC
  finalItems.sort((a, b) => {
    const timeA = new Date(a.created_at).getTime();
    const timeB = new Date(b.created_at).getTime();
    if (timeA !== timeB) {
      return timeB - timeA; // DESC
    }
    return String(b.id).localeCompare(String(a.id)); // DESC by ID
  });
  
  return finalItems;
}

describe('TopicPage Stable Pagination', () => {
  const createPoll = (id: string, createdAt: string, title: string): PollSummary => ({
    id,
    title,
    decision_type: 'level_b',
    created_at: createdAt,
    labels: [{ name: 'Test', slug: 'test' }]
  });

  it('should maintain stable order after two merges', () => {
    // Initial items
    const initialItems = [
      createPoll('poll-1', '2024-01-01T10:00:00Z', 'First Poll'),
      createPoll('poll-2', '2024-01-01T11:00:00Z', 'Second Poll'),
      createPoll('poll-3', '2024-01-01T12:00:00Z', 'Third Poll')
    ];
    
    // First merge - add some new items
    const firstNewItems = [
      createPoll('poll-4', '2024-01-01T13:00:00Z', 'Fourth Poll'),
      createPoll('poll-5', '2024-01-01T14:00:00Z', 'Fifth Poll')
    ];
    
    const afterFirstMerge = mergeAndSortPolls(initialItems, firstNewItems);
    
    // Second merge - add more items and update some existing ones
    const secondNewItems = [
      createPoll('poll-6', '2024-01-01T15:00:00Z', 'Sixth Poll'),
      createPoll('poll-1', '2024-01-01T10:00:00Z', 'First Poll Updated'), // Update existing
      createPoll('poll-7', '2024-01-01T16:00:00Z', 'Seventh Poll')
    ];
    
    const afterSecondMerge = mergeAndSortPolls(afterFirstMerge, secondNewItems);
    
    // Verify order is stable and correct (newest first, then by ID DESC)
    expect(afterSecondMerge).toHaveLength(7);
    expect(afterSecondMerge.map(p => p.id)).toEqual([
      'poll-7', // newest
      'poll-6',
      'poll-5',
      'poll-4',
      'poll-3',
      'poll-2',
      'poll-1'  // oldest
    ]);
    
    // Verify the updated item was applied
    expect(afterSecondMerge[6].title).toBe('First Poll Updated');
  });

  it('should handle items with same timestamp correctly', () => {
    const initialItems = [
      createPoll('poll-a', '2024-01-01T10:00:00Z', 'Poll A'),
      createPoll('poll-b', '2024-01-01T10:00:00Z', 'Poll B'), // Same time as A
      createPoll('poll-c', '2024-01-01T11:00:00Z', 'Poll C')
    ];
    
    const newItems = [
      createPoll('poll-d', '2024-01-01T10:00:00Z', 'Poll D'), // Same time as A and B
      createPoll('poll-e', '2024-01-01T12:00:00Z', 'Poll E')
    ];
    
    const result = mergeAndSortPolls(initialItems, newItems);
    
    // Should be sorted by time DESC, then by ID DESC for same timestamps
    expect(result.map(p => p.id)).toEqual([
      'poll-e', // newest
      'poll-c',
      'poll-d', // same time as A and B, but 'd' > 'b' > 'a' alphabetically
      'poll-b',
      'poll-a'
    ]);
  });

  it('should preserve order when merging with empty arrays', () => {
    // Create items that are already in the expected sort order (newest first, then by ID DESC)
    const initialItems = [
      createPoll('poll-2', '2024-01-01T11:00:00Z', 'Second Poll'), // newer
      createPoll('poll-1', '2024-01-01T10:00:00Z', 'First Poll')   // older
    ];
    
    // Merge with empty array
    const afterEmptyMerge = mergeAndSortPolls(initialItems, []);
    
    // Should be identical since items are already in correct order
    expect(afterEmptyMerge).toEqual(initialItems);
    
    // Merge empty with items
    const afterEmptyFirst = mergeAndSortPolls([], initialItems);
    
    // Should be identical to initial items
    expect(afterEmptyFirst).toEqual(initialItems);
  });

  it('should handle duplicate items in input arrays', () => {
    const initialItems = [
      createPoll('poll-1', '2024-01-01T10:00:00Z', 'First Poll'),
      createPoll('poll-1', '2024-01-01T10:00:00Z', 'First Poll Duplicate'), // Duplicate
      createPoll('poll-2', '2024-01-01T11:00:00Z', 'Second Poll')
    ];
    
    const newItems = [
      createPoll('poll-2', '2024-01-01T11:00:00Z', 'Second Poll Duplicate'), // Duplicate
      createPoll('poll-3', '2024-01-01T12:00:00Z', 'Third Poll')
    ];
    
    const result = mergeAndSortPolls(initialItems, newItems);
    
    // Should deduplicate and maintain correct order
    expect(result).toHaveLength(3);
    expect(result.map(p => p.id)).toEqual(['poll-3', 'poll-2', 'poll-1']);
    
    // Last occurrence of each ID should be used
    expect(result[1].title).toBe('Second Poll Duplicate');
    expect(result[2].title).toBe('First Poll Duplicate');
  });

  it('should maintain stability across multiple identical merges', () => {
    const baseItems = [
      createPoll('poll-1', '2024-01-01T10:00:00Z', 'First Poll'),
      createPoll('poll-2', '2024-01-01T11:00:00Z', 'Second Poll')
    ];
    
    const newItems = [
      createPoll('poll-3', '2024-01-01T12:00:00Z', 'Third Poll')
    ];
    
    // Perform the same merge twice
    const firstResult = mergeAndSortPolls(baseItems, newItems);
    const secondResult = mergeAndSortPolls(baseItems, newItems);
    
    // Results should be identical
    expect(firstResult).toEqual(secondResult);
    
    // Order should be stable
    expect(firstResult.map(p => p.id)).toEqual(['poll-3', 'poll-2', 'poll-1']);
  });

  it('should handle edge case with single items', () => {
    const singleItem = [createPoll('poll-1', '2024-01-01T10:00:00Z', 'Single Poll')];
    
    const result = mergeAndSortPolls(singleItem, singleItem);
    
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('poll-1');
  });
});
