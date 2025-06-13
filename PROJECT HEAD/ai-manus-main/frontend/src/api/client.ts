// Backend API client configuration
import axios, { AxiosError } from 'axios';

// API configuration
export const API_CONFIG = {
  host: import.meta.env.VITE_API_URL || '',
  version: 'v1',
  timeout: 30000, // Request timeout in milliseconds
};

// Complete API base URL
export const BASE_URL = API_CONFIG.host 
  ? `${API_CONFIG.host}/api/${API_CONFIG.version}` 
  : `/api/${API_CONFIG.version}`;

// Unified response format
export interface ApiResponse<T> {
  code: number;
  msg: string;
  data: T;
}

// Error format
export interface ApiError {
  code: number;
  message: string;
  details?: unknown;
}

// Create axios instance
export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor, can add authentication token etc.
apiClient.interceptors.request.use(
  (config) => {
    // Authentication token can be added here
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor, unified error handling
apiClient.interceptors.response.use(
  (response) => {
    // Check backend response format
    if (response.data && typeof response.data.code === 'number') {
      // If it's a business logic error (code not 0), convert to error handling
      if (response.data.code !== 0) {
        const apiError: ApiError = {
          code: response.data.code,
          message: response.data.msg || 'Unknown error',
          details: response.data
        };
        return Promise.reject(apiError);
      }
    }
    return response;
  },
  (error: AxiosError) => {
    const apiError: ApiError = {
      code: 500,
      message: 'Request failed',
    };

    if (error.response) {
      const status = error.response.status;
      apiError.code = status;
      
      // Try to extract detailed error information from response content
      if (error.response.data && typeof error.response.data === 'object') {
        const data = error.response.data as any;
        if (data.code && data.msg) {
          apiError.code = data.code;
          apiError.message = data.msg;
        } else {
          apiError.message = data.message || error.response.statusText || 'Request failed';
        }
        apiError.details = data;
      } else {
        apiError.message = error.response.statusText || 'Request failed';
      }
    } else if (error.request) {
      apiError.code = 503;
      apiError.message = 'Network error, please check your connection';
    }

    console.error('API Error:', apiError);
    return Promise.reject(apiError);
  }
); 