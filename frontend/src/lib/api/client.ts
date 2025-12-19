import axios, { type AxiosError, type AxiosInstance } from 'axios';
import { API_BASE_URL } from '@/lib/constants';

// Create Axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add session ID, etc.)
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const sessionId = localStorage.getItem('graphlit_session_id');
      if (sessionId) {
        config.headers['X-Session-ID'] = sessionId;
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor (handle errors globally)
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      console.error(`API Error: ${error.response.status}`, error.response.data);
    } else if (error.request) {
      console.error('Network Error: No response received');
    } else {
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  },
);
