import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Required for HTTP-only cookies
});

// Request interceptor for adding auth tokens if needed
apiClient.interceptors.request.use(
  (config) => {
    // TODO: Add auth token if available
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401/403 for auth, redirect to login
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Only redirect if we're not already on the login or register page
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        // Clear any auth state before redirecting
        // Note: This relies on React Query cache being cleared by useAuth hook on 401
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;

