import apiClient from './api';
import type { UserPreferences, UserPreferencesUpdate } from '../types/user';

/**
 * Get current user's preferences
 * @returns UserPreferences object or null if not found (404)
 * @throws Error if authentication fails (401) or other server errors
 */
export async function getPreferences(): Promise<UserPreferences | null> {
  try {
    const response = await apiClient.get<UserPreferences>(
      '/api/v1/users/me/preferences'
    );
    return response.data;
  } catch (error: any) {
    // Handle 404 by returning null (preferences will be created on first PUT)
    if (error.response?.status === 404) {
      return null;
    }
    // Re-throw other errors (401, 500, etc.)
    throw error;
  }
}

/**
 * Update current user's preferences
 * Creates preferences if they don't exist
 * @param preferences - Partial preferences object (holding_period and/or risk_tolerance)
 * @returns Updated UserPreferences object
 * @throws Error with validation message for invalid enum values (400) or authentication fails (401)
 */
export async function updatePreferences(
  preferences: UserPreferencesUpdate
): Promise<UserPreferences> {
  const response = await apiClient.put<UserPreferences>(
    '/api/v1/users/me/preferences',
    preferences
  );
  return response.data;
}

