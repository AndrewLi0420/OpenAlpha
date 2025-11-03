import { useQuery } from '@tanstack/react-query';
import { checkTierLimit } from '../services/tier';
import type { TierStatus } from '../services/tier';

const TIER_QUERY_KEY = ['tier-status', 'current-user'];

/**
 * React Query hook for tier status management
 * @returns Tier status data, loading state, and error state
 */
export function useTier() {
  const {
    data: tierStatus,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<TierStatus>({
    queryKey: TIER_QUERY_KEY,
    queryFn: checkTierLimit,
    retry: false,
    staleTime: 1 * 60 * 1000, // Consider data fresh for 1 minute
    refetchOnWindowFocus: true,
  });

  return {
    tier: tierStatus?.tier ?? 'free',
    stockCount: tierStatus?.stock_count ?? 0,
    stockLimit: tierStatus?.stock_limit ?? null,
    canAddMore: tierStatus?.can_add_more ?? false,
    isPremium: tierStatus?.tier === 'premium',
    isLoading,
    isError,
    error,
    refetch,
  };
}

