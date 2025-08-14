import { flags } from '../config/flags';
import type { Poll } from '../types';

/**
 * Get the correct href for a poll based on its decision type and feature flags
 * @param poll The poll object
 * @returns The correct href for the poll
 */
export function getProposalHref(poll: Poll): string {
  if (flags.compassEnabled && poll.decision_type === 'level_a') {
    return `/compass/${poll.id}`;
  }
  return `/proposals/${poll.id}`;
}

/**
 * Get the correct href for a poll by ID and decision type
 * @param id The poll ID
 * @param decisionType The decision type
 * @returns The correct href for the poll
 */
export function getProposalHrefById(id: string, decisionType: string): string {
  if (flags.compassEnabled && decisionType === 'level_a') {
    return `/compass/${id}`;
  }
  return `/proposals/${id}`;
}
