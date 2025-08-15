import { flags } from '../config/flags';
import type { Poll } from '../types';

/**
 * Get the correct href for a poll based on its decision type and feature flags
 * @param poll The poll object
 * @returns The correct href for the poll
 */
export function getProposalHref(poll: Poll): string {
  // For level_a proposals, use the compass route if enabled
  if (poll.decision_type === 'level_a' && flags.compassEnabled) {
    return `/compass/${poll.id}`;
  }
  // All other proposals use the /proposals/ route
  return `/proposals/${poll.id}`;
}

/**
 * Get the correct href for a poll by ID and decision type
 * @param id The poll ID
 * @param decisionType The decision type
 * @returns The correct href for the poll
 */
export function getProposalHrefById(id: string, decisionType: string): string {
  // For level_a proposals, use the compass route if enabled
  if (decisionType === 'level_a' && flags.compassEnabled) {
    return `/compass/${id}`;
  }
  // All other proposals use the /proposals/ route
  return `/proposals/${id}`;
}
