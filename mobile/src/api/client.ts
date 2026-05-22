import { storage } from '../utils/storage';

export const BASE_URL =
  (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_API_URL) ||
  'http://localhost:8000';

const API_V1 = `${BASE_URL}/api/v1`;

const FETCH_TIMEOUT = 10000; // 10 seconds

async function fetchWithTimeout(url: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
  try {
    const res = await fetch(url, { ...init, signal: controller.signal });
    clearTimeout(id);
    return res;
  } catch (e: any) {
    clearTimeout(id);
    if (e.name === 'AbortError') throw new Error('Request timed out. Is the backend running?');
    throw new Error('Network error. Is the backend running?');
  }
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = await storage.getRefreshToken();
  if (!refresh) return null;
  try {
    const res = await fetchWithTimeout(`${API_V1}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (data.access_token) {
      await storage.setTokens(data.access_token, refresh);
      return data.access_token;
    }
    return null;
  } catch {
    return null;
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  noAuth?: boolean;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const token = options.noAuth ? null : await storage.getAccessToken();

  const url = `${API_V1}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let res = await fetchWithTimeout(url, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  // Token refresh retry on 401
  if (res.status === 401 && !options.noAuth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.Authorization = `Bearer ${newToken}`;
      res = await fetchWithTimeout(url, {
        method: options.method || 'GET',
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
      });
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || 'Request failed');
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// Convenience wrappers
const get = <T>(path: string) => apiRequest<T>(path);
const post = <T>(path: string, body: unknown) => apiRequest<T>(path, { method: 'POST', body });

export const api = {
  auth: {
    login: (phone: string, password: string) =>
      post('/auth/login', { phone, password }),
    sendOtp: (phone: string) =>
      post('/auth/send-otp', { phone }),
    verifyOtp: (phone: string, otp: string) =>
      post('/auth/verify-otp', { phone, otp, purpose: 'login' }),
    registerSendOtp: (phone: string, full_name: string) =>
      post('/auth/register/send-phone-otp', { phone, full_name }),
    registerVerifyOtp: (phone: string, otp: string, full_name: string, email?: string) =>
      post('/auth/register/verify-phone', { phone, otp, full_name, email }),
    me: () =>
      get('/auth/me'),
    logout: () =>
      post('/auth/logout', {}),
  },
  cars: {
    browse: (params: Record<string, string | number | undefined>) => {
      const q = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v != null) q.set(k, String(v));
      });
      return get(`/vehicles?${q.toString()}`);
    },
    detail: (id: string) =>
      get(`/vehicles/${id}`),
    reviews: (id: string) =>
      get(`/vehicles/${id}/reviews`),
  },
  bookings: {
    preview: (data: unknown) =>
      post('/bookings/preview', data),
    create: (data: unknown) =>
      post('/bookings', data),
    list: () =>
      get('/bookings'),
    cancel: (id: string, reason?: string) =>
      post(`/bookings/${id}/cancel`, { reason }),
  },
  payments: {
    createOrder: (booking_id: string) =>
      post('/payments/create-order', { booking_id }),
  },
  reviews: {
    submit: (data: unknown) =>
      post('/reviews', data),
    pending: () =>
      get('/reviews/pending'),
  },
  kyc: {
    upload: async (formData: FormData) => {
      const token = await storage.getAccessToken();
      const url = `${API_V1}/kyc/documents`;
      let res = await fetchWithTimeout(url, {
        method: 'POST',
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      });
      if (res.status === 401 && token) {
        const newToken = await refreshAccessToken();
        if (newToken) {
          res = await fetchWithTimeout(url, {
            method: 'POST',
            headers: { Authorization: `Bearer ${newToken}` },
            body: formData,
          });
        }
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Upload failed');
      }
      return res.json();
    },
    documents: () =>
      get('/kyc/documents'),
    status: () =>
      get('/kyc/verify-status'),
  },
};
