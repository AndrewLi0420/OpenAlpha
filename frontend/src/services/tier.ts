import apiClient from './api';

/**
 * Tier status response from API
 */
export interface TierStatus {
  tier: 'free' | 'premium';
  stock_count: number;
  stock_limit: number | null;
  can_add_more: boolean;
}

/**
 * Get current user's tier status
 * @returns TierStatus object with tier, stock count, limits, and can_add_more flag
 * @throws Error if authentication fails (401) or other server errors
 */
export async function checkTierLimit(): Promise<TierStatus> {
  const response = await apiClient.get<TierStatus>(
    '/api/v1/users/me/tier-status'
  );
  return response.data;
}

