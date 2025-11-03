import apiClient from './api';

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
  is_verified: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  tier: 'free' | 'premium';
  is_verified: boolean;
}

export interface ApiError {
  error: {
    type: string;
    message: string;
    detail?: string;
  };
}

/**
 * Register a new user
 * @param email - User email address
 * @param password - User password (minimum 8 characters, complexity required)
 * @returns User object with id, email, and is_verified
 * @throws Error with user-friendly message for validation/duplicate email errors
 */
export async function register(email: string, password: string): Promise<RegisterResponse> {
  const response = await apiClient.post<RegisterResponse>('/api/v1/auth/register', {
    email,
    password,
  });
  return response.data;
}

/**
 * Login with email and password
 * JWT token is stored in HTTP-only cookie by backend
 * FastAPI Users login endpoint expects form data (application/x-www-form-urlencoded)
 * @param email - User email address
 * @param password - User password
 * @returns LoginResponse with access_token and token_type
 * @throws Error with generic message "Invalid email or password" for auth failures
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  try {
    // FastAPI Users login endpoint expects form data with 'username' field (email)
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await apiClient.post<LoginResponse>(
      '/api/v1/auth/login',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    // Cookie is automatically set by browser (HTTP-only cookie)
    return response.data;
  } catch (error: any) {
    // Generic error message for security (doesn't reveal if email exists)
    if (error.response?.status === 401 || error.response?.status === 400) {
      throw new Error('Invalid email or password');
    }
    throw error;
  }
}

/**
 * Logout current user
 * Clears HTTP-only cookie via backend logout endpoint
 */
export async function logout(): Promise<void> {
  try {
    await apiClient.post('/api/v1/auth/logout');
    // Cookie is cleared by backend response
  } catch (error) {
    // Even if logout fails, we should clear local state
    console.error('Logout error:', error);
  }
}

/**
 * Get current authenticated user
 * Verifies session via HTTP-only cookie
 * @returns User object if authenticated, throws error if not
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/api/v1/users/me');
  return response.data;
}

