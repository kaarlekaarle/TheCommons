import type { PollOption, PollResults } from '../types';

export interface PrimaryOptionResult {
  primaryId: string;
  alternateId: string;
  tie: boolean;
}

/**
 * Compute which option should be primary based on vote results
 * @param options - Array of poll options
 * @param results - Poll results with vote counts
 * @param threshold - Percentage difference threshold for tie (default 5%)
 * @returns Object with primaryId, alternateId, and tie flag
 */
export function computePrimaryOption(
  options: PollOption[],
  results?: PollResults,
  threshold = 0.05
): PrimaryOptionResult {
  // Handle edge cases
  if (!options || options.length === 0) {
    return { primaryId: '', alternateId: '', tie: true };
  }

  if (options.length === 1) {
    return { primaryId: options[0].id, alternateId: '', tie: false };
  }

  // If no results or no votes, treat as tie
  if (!results || !results.total_votes || results.total_votes === 0) {
    return { 
      primaryId: options[0].id, 
      alternateId: options[1]?.id || '', 
      tie: true 
    };
  }

  // Calculate vote shares for each option
  const optionShares = options.map(option => {
    const resultOption = results.options.find(r => r.option_id === option.id);
    const voteCount = resultOption?.votes || 0;
    const share = voteCount / results.total_votes;
    return { id: option.id, share, votes: voteCount };
  });

  // Sort by vote share (descending)
  optionShares.sort((a, b) => b.share - a.share);

  const [first, second] = optionShares;
  
  // Check if it's a tie (within threshold)
  const difference = first.share - second.share;
  const isTie = difference <= threshold;

  return {
    primaryId: first.id,
    alternateId: second.id,
    tie: isTie
  };
}

/**
 * Type guard to check if a result indicates a tie
 */
export function isTie(result: PrimaryOptionResult): boolean {
  return result.tie;
}
