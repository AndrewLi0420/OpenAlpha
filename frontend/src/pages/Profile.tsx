import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../hooks/useAuth';
import { useTier } from '../hooks/useTier';
import { getPreferences, updatePreferences } from '../services/userPreferences';
import type { UserPreferences, UserPreferencesUpdate } from '../types/user';

const PREFERENCES_QUERY_KEY = ['preferences', 'current-user'];

export default function Profile() {
  const { user } = useAuth();
  const { tier, stockCount, stockLimit, canAddMore, isPremium, isLoading: tierLoading } = useTier();
  const queryClient = useQueryClient();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch preferences
  const {
    data: preferences,
    isLoading,
    isError,
    error,
  } = useQuery<UserPreferences | null>({
    queryKey: PREFERENCES_QUERY_KEY,
    queryFn: getPreferences,
    retry: false,
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });

  // Local state for form (defaults if preferences not loaded yet)
  const [holdingPeriod, setHoldingPeriod] = useState<UserPreferences['holding_period']>('daily');
  const [riskTolerance, setRiskTolerance] = useState<UserPreferences['risk_tolerance']>('medium');

  // Update local state when preferences load
  useEffect(() => {
    if (preferences) {
      setHoldingPeriod(preferences.holding_period);
      setRiskTolerance(preferences.risk_tolerance);
    }
  }, [preferences]);

  // Update preferences mutation
  const updateMutation = useMutation({
    mutationFn: (prefs: UserPreferencesUpdate) => updatePreferences(prefs),
    onSuccess: (updatedPrefs) => {
      // Update React Query cache
      queryClient.setQueryData(PREFERENCES_QUERY_KEY, updatedPrefs);
      // Update local state
      setHoldingPeriod(updatedPrefs.holding_period);
      setRiskTolerance(updatedPrefs.risk_tolerance);
      // Show success message
      setSuccessMessage('Preferences saved successfully!');
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    },
    onError: (error: any) => {
      console.error('Failed to update preferences:', error);
      setSuccessMessage(null);
    },
  });

  const handleSave = () => {
    // Always send both values to ensure preferences are created if they don't exist
    const updates: UserPreferencesUpdate = {
      holding_period: holdingPeriod,
      risk_tolerance: riskTolerance,
    };

    // Check if there are actual changes
    const hasChanges = !preferences || 
      holdingPeriod !== preferences.holding_period || 
      riskTolerance !== preferences.risk_tolerance;

    if (hasChanges) {
      updateMutation.mutate(updates);
    } else {
      setSuccessMessage('No changes to save');
      setTimeout(() => setSuccessMessage(null), 3000);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Profile</h1>

      {/* User Info Section */}
      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 mb-6">
          <h2 className="text-xl font-semibold mb-4">Account Information</h2>
          {user && (
            <div className="space-y-2 text-gray-300">
              <p>
                <strong>Email:</strong> {user.email}
              </p>
              <p>
                <strong>Tier:</strong>{' '}
                <span className={`inline-block px-2 py-1 rounded text-sm font-medium ${
                  isPremium 
                    ? 'bg-green-900 text-green-300' 
                    : 'bg-blue-900 text-blue-300'
                }`}>
                  {isPremium ? 'Premium - Unlimited' : `Free Tier - Tracking ${stockCount}/${stockLimit ?? 5} stocks`}
                </span>
                {isPremium && (
                  <span className="ml-2 text-green-400">✨</span>
                )}
              </p>
              <p>
                <strong>Verified:</strong> {user.is_verified ? 'Yes' : 'No'}
              </p>
            </div>
          )}
        </div>

        {/* Preferences Section */}
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
          <h2 className="text-xl font-semibold mb-4">Investment Preferences</h2>

          {isLoading && (
            <div className="text-gray-400">Loading preferences...</div>
          )}

          {isError && error && (
            <div className="mb-4 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300">
              {error instanceof Error
                ? error.message
                : 'Failed to load preferences'}
            </div>
          )}

          {!isLoading && !isError && (
            <div className="space-y-6">
              {/* Holding Period Dropdown */}
              <div>
                <label
                  htmlFor="holding-period"
                  className="block text-sm font-medium text-gray-300 mb-2"
                >
                  Holding Period
                </label>
                <select
                  id="holding-period"
                  value={holdingPeriod}
                  onChange={(e) =>
                    setHoldingPeriod(e.target.value as UserPreferences['holding_period'])
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
                {preferences && (
                  <p className="mt-1 text-sm text-gray-400">
                    Saved: {preferences.holding_period.charAt(0).toUpperCase() + preferences.holding_period.slice(1)}
                  </p>
                )}
                {!preferences && (
                  <p className="mt-1 text-sm text-gray-400">
                    No preferences saved yet. Select your preference and click Save.
                  </p>
                )}
              </div>

              {/* Risk Tolerance Dropdown */}
              <div>
                <label
                  htmlFor="risk-tolerance"
                  className="block text-sm font-medium text-gray-300 mb-2"
                >
                  Risk Tolerance
                </label>
                <select
                  id="risk-tolerance"
                  value={riskTolerance}
                  onChange={(e) =>
                    setRiskTolerance(e.target.value as UserPreferences['risk_tolerance'])
                  }
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
                {preferences && (
                  <p className="mt-1 text-sm text-gray-400">
                    Saved: {preferences.risk_tolerance.charAt(0).toUpperCase() + preferences.risk_tolerance.slice(1)}
                  </p>
                )}
                {!preferences && (
                  <p className="mt-1 text-sm text-gray-400">
                    No preferences saved yet. Select your preference and click Save.
                  </p>
                )}
              </div>

              {/* Save Button */}
              <button
                onClick={handleSave}
                disabled={updateMutation.isPending}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors font-medium"
              >
                {updateMutation.isPending ? 'Saving...' : 'Save Preferences'}
              </button>

              {/* Success/Error Messages */}
              {successMessage && (
                <div className="p-4 bg-green-900/30 border border-green-700 rounded-lg text-green-300">
                  {successMessage}
                </div>
              )}

              {updateMutation.isError && (
                <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-300">
                  Failed to save preferences. Please try again.
                </div>
              )}
            </div>
          )}
        </div>
    </div>
  );
}

