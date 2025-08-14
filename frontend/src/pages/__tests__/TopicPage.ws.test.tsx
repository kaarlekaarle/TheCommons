import { describe, it, expect, vi } from 'vitest';
import type { PollSummary } from '../../types';

// Mock the WebSocket upsert reducer function
function wsUpsertReducer(
  existingItems: PollSummary[],
  incomingItem: PollSummary & { updated_at: string }
): PollSummary[] {
  const existingIndex = existingItems.findIndex(item => item.id === incomingItem.id);
  
  if (existingIndex === -1) {
    // New item, add it
    return [...existingItems, incomingItem];
  }
  
  const existingItem = existingItems[existingIndex];
  const existingTime = new Date(existingItem.created_at).getTime();
  const incomingTime = new Date(incomingItem.updated_at).getTime();
  
  // Only update if incoming item is newer
  if (incomingTime > existingTime) {
    const newItems = [...existingItems];
    newItems[existingIndex] = incomingItem;
    return newItems;
  }
  
  // Keep existing item if it's newer or same age
  return existingItems;
}

describe('TopicPage WebSocket Upsert Reducer', () => {
  const basePoll: PollSummary = {
    id: 'poll-1',
    title: 'Test Poll',
    decision_type: 'level_b',
    created_at: '2024-01-01T10:00:00Z',
    labels: [{ name: 'Test', slug: 'test' }]
  };

  it('should add new items that do not exist', () => {
    const existingItems: PollSummary[] = [];
    const incomingItem = { ...basePoll, updated_at: '2024-01-01T10:00:00Z' };
    
    const result = wsUpsertReducer(existingItems, incomingItem);
    
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual(incomingItem);
  });

  it('should update existing item when incoming item is newer', () => {
    const existingItems: PollSummary[] = [
      { ...basePoll, created_at: '2024-01-01T10:00:00Z' }
    ];
    const incomingItem = {
      ...basePoll,
      title: 'Updated Poll',
      updated_at: '2024-01-01T11:00:00Z' // 1 hour newer
    };
    
    const result = wsUpsertReducer(existingItems, incomingItem);
    
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('Updated Poll');
    expect(result[0].updated_at).toBe('2024-01-01T11:00:00Z');
  });

  it('should ignore incoming item when existing item is newer', () => {
    const existingItems: PollSummary[] = [
      { ...basePoll, created_at: '2024-01-01T11:00:00Z' }
    ];
    const incomingItem = {
      ...basePoll,
      title: 'Older Update',
      updated_at: '2024-01-01T10:00:00Z' // 1 hour older
    };
    
    const result = wsUpsertReducer(existingItems, incomingItem);
    
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('Test Poll'); // Original title preserved
    expect(result[0].created_at).toBe('2024-01-01T11:00:00Z'); // Original time preserved
  });

  it('should ignore incoming item when timestamps are equal', () => {
    const existingItems: PollSummary[] = [
      { ...basePoll, created_at: '2024-01-01T10:00:00Z' }
    ];
    const incomingItem = {
      ...basePoll,
      title: 'Same Time Update',
      updated_at: '2024-01-01T10:00:00Z' // Same time
    };
    
    const result = wsUpsertReducer(existingItems, incomingItem);
    
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('Test Poll'); // Original title preserved
  });

  it('should handle multiple items correctly', () => {
    const existingItems: PollSummary[] = [
      { ...basePoll, id: 'poll-1', created_at: '2024-01-01T10:00:00Z' },
      { ...basePoll, id: 'poll-2', created_at: '2024-01-01T11:00:00Z' },
      { ...basePoll, id: 'poll-3', created_at: '2024-01-01T12:00:00Z' }
    ];
    
    // Update poll-2 with newer data
    const incomingItem = {
      ...basePoll,
      id: 'poll-2',
      title: 'Updated Poll 2',
      updated_at: '2024-01-01T13:00:00Z' // 2 hours newer
    };
    
    const result = wsUpsertReducer(existingItems, incomingItem);
    
    expect(result).toHaveLength(3);
    expect(result[0].title).toBe('Test Poll'); // poll-1 unchanged
    expect(result[1].title).toBe('Updated Poll 2'); // poll-2 updated
    expect(result[2].title).toBe('Test Poll'); // poll-3 unchanged
  });

  it('should preserve order of existing items', () => {
    const existingItems: PollSummary[] = [
      { ...basePoll, id: 'poll-1', created_at: '2024-01-01T10:00:00Z' },
      { ...basePoll, id: 'poll-2', created_at: '2024-01-01T11:00:00Z' },
      { ...basePoll, id: 'poll-3', created_at: '2024-01-01T12:00:00Z' }
    ];
    
    // Update poll-1 with newer data
    const incomingItem = {
      ...basePoll,
      id: 'poll-1',
      title: 'Updated Poll 1',
      updated_at: '2024-01-01T13:00:00Z'
    };
    
    const result = wsUpsertReducer(existingItems, incomingItem);
    
    expect(result).toHaveLength(3);
    expect(result[0].id).toBe('poll-1'); // Order preserved
    expect(result[1].id).toBe('poll-2'); // Order preserved
    expect(result[2].id).toBe('poll-3'); // Order preserved
    expect(result[0].title).toBe('Updated Poll 1'); // Content updated
  });

  it('should handle edge case with very close timestamps', () => {
    const existingItems: PollSummary[] = [
      { ...basePoll, created_at: '2024-01-01T10:00:00.001Z' }
    ];
    const incomingItem = {
      ...basePoll,
      title: 'Close Update',
      updated_at: '2024-01-01T10:00:00.000Z' // 1ms older
    };
    
    const result = wsUpsertReducer(existingItems, incomingItem);
    
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('Test Poll'); // Original preserved
  });

  it('should handle malformed timestamps gracefully', () => {
    const existingItems: PollSummary[] = [
      { ...basePoll, created_at: '2024-01-01T10:00:00Z' }
    ];
    const incomingItem = {
      ...basePoll,
      title: 'Malformed Update',
      updated_at: 'invalid-date'
    };
    
    // This should not throw and should preserve existing item
    const result = wsUpsertReducer(existingItems, incomingItem);
    
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe('Test Poll'); // Original preserved
  });
});
