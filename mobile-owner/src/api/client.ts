import { storage } from '../utils/storage';

export const BASE_URL =
  (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_API_URL) ||
  'http://localhost:8000';

const API_V1 = `${BASE_URL}/api/v1`;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = await storage.getRefreshToken();
  if (!refresh) return null;
  try {
    const res = await fetch(`${API_V1}/auth/refresh`, {
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

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = options.noAuth ? null : await storage.getAccessToken();
  const url = `${API_V1}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  let res = await fetch(url, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (res.status === 401 && !options.noAuth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers.Authorization = `Bearer ${newToken}`;
      res = await fetch(url, {
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

const get = <T>(path: string) => apiRequest<T>(path);
const post = <T>(path: string, body: unknown) => apiRequest<T>(path, { method: 'POST', body });
const patch = <T>(path: string, body: unknown) => apiRequest<T>(path, { method: 'PATCH', body });
const del = <T>(path: string) => apiRequest<T>(path, { method: 'DELETE' });

export const api = {
  auth: {
    sendOtp: (phone: string) => post('/auth/send-otp', { phone }),
    verifyOtp: (phone: string, otp: string) => post('/auth/verify-otp', { phone, otp, purpose: 'login' }),
    registerSendOtp: (phone: string, full_name: string) => post('/auth/register/send-phone-otp', { phone, full_name }),
    registerVerifyOtp: (phone: string, otp: string, full_name: string, email?: string) =>
      post('/auth/register/verify-phone', { phone, otp, full_name, email }),
    me: () => get('/auth/me'),
    logout: () => post('/auth/logout', {}),
  },
  owner: {
    cars: () => get('/owner/cars'),
    addCar: (data: unknown) => post('/owner/cars', data),
    updateCar: (id: string, data: unknown) => patch(`/owner/cars/${id}`, data),
    deleteCar: (id: string) => del(`/owner/cars/${id}`),
    submitCar: (id: string) => post(`/owner/cars/${id}/submit`, {}),
    uploadImage: async (carId: string, uri: string, isPrimary: boolean) => {
      const token = await storage.getAccessToken();
      const formData = new FormData();
      formData.append('file', {
        uri,
        name: 'image.jpg',
        type: 'image/jpeg',
      } as any);
      formData.append('is_primary', String(isPrimary));
      const url = `${API_V1}/owner/cars/${carId}/images`;
      let res = await fetch(url, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (res.status === 401 && token) {
        const newToken = await refreshAccessToken();
        if (newToken) {
          res = await fetch(url, {
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
    bookings: () => get('/owner/bookings'),
    bookingDetail: (id: string) => get(`/owner/bookings/${id}`),
    acceptBooking: (id: string) => post(`/owner/bookings/${id}/accept`, {}),
    earnings: () => get('/owner/earnings'),
    earningsMonthly: (months = 6) => get(`/owner/earnings/monthly?months=${months}`),
    availability: (carId: string) => get('/owner/availability'),
    blockSlot: (data: unknown) => post('/owner/availability', data),
    unblockSlot: (id: string) => del(`/owner/availability/${id}`),
  },
  kyc: {
    upload: async (formData: FormData) => {
      const token = await storage.getAccessToken();
      const url = `${API_V1}/kyc/documents`;
      let res = await fetch(url, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (res.status === 401 && token) {
        const newToken = await refreshAccessToken();
        if (newToken) {
          res = await fetch(url, { method: 'POST', headers: { Authorization: `Bearer ${newToken}` }, body: formData });
        }
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Upload failed');
      }
      return res.json();
    },
    documents: () => get('/kyc/documents'),
    status: () => get('/kyc/verify-status'),
  },
};
