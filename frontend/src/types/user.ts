/**
 * User preferences types
 */

export type HoldingPeriod = 'daily' | 'weekly' | 'monthly';
export type RiskTolerance = 'low' | 'medium' | 'high';

export interface UserPreferences {
  id: string;
  user_id: string;
  holding_period: HoldingPeriod;
  risk_tolerance: RiskTolerance;
  updated_at: string; // ISO 8601 datetime string
}

export interface UserPreferencesUpdate {
  holding_period?: HoldingPeriod;
  risk_tolerance?: RiskTolerance;
}

