const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  full_name: string;
  email: string | null;
  phone: string;
  role: "customer" | "owner" | "admin";
  is_verified: boolean;
  avatar_url: string | null;
}

export interface VehicleListItem {
  id: string;
  make: string;
  model: string;
  variant: string | null;
  year: number;
  city: string;
  state: string;
  fuel_type: string;
  transmission: string;
  seating: number;
  price_per_hour: number;
  price_per_day: number;
  primary_image: string | null;
  avg_rating: number | null;
  review_count: number;
}

export interface VehicleDetail extends VehicleListItem {
  owner_id: string;
  color: string;
  mileage_kmpl: number | null;
  latitude: number | null;
  longitude: number | null;
  address: string | null;
  security_deposit: number;
  features: Record<string, boolean>;
  images: { id: string; url: string; is_primary: boolean; sort_order: number }[];
  status: string;
}

export interface PaginatedVehicles {
  items: VehicleListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface BrowseParams {
  city?: string;
  fuel_type?: string;
  transmission?: string;
  min_seating?: number;
  min_price_day?: number;
  max_price_day?: number;
  pickup_time?: string;
  dropoff_time?: string;
  sort_by?: "price_asc" | "price_desc" | "rating" | "newest";
  page?: number;
  limit?: number;
}

export interface PricingBreakdown {
  duration_hours: number;
  duration_days: number;
  base_amount: number;
  discount_amount: number;
  tax_amount: number;
  security_deposit: number;
  total_amount: number;
  currency: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Booking {
  id: string;
  vehicle_id: string;
  customer_id: string;
  pickup_time: string;
  dropoff_time: string;
  status: string;
  total_amount: number;
  base_amount: number;
  created_at: string;
}

export interface OwnerVehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  color: string;
  registration_number: string;
  status: string;
  kyc_status: string;
  price_per_hour: number;
  price_per_day: number;
  city: string;
  images: { id: string; url: string; is_primary: boolean }[];
}

export interface EarningsSummary {
  total_earnings: number;
  this_month: number;
  last_month: number;
  pending_payout: number;
  total_bookings: number;
  completed_bookings: number;
  avg_rating: number | null;
  top_car: string | null;
}

export interface MonthlyEarning {
  month: string;
  amount: number;
  bookings: number;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

function getAuthHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, err.detail ?? "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

function buildQuery(params: Record<string, unknown>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

// ── API ────────────────────────────────────────────────────────────────────────

export const api = {
  auth: {
    register: (data: { full_name: string; phone: string; password: string; role?: string }) =>
      request<User>("/auth/register", { method: "POST", body: JSON.stringify(data) }),

    login: (phone: string, password: string): Promise<TokenResponse> =>
      request("/auth/login", { method: "POST", body: JSON.stringify({ phone, password }) }),

    sendOtp: (phone: string) =>
      request<{ message: string; otp?: string }>("/auth/send-otp", {
        method: "POST",
        body: JSON.stringify({ phone, purpose: "login" }),
      }),

    verifyOtp: (phone: string, otp: string): Promise<TokenResponse> =>
      request("/auth/verify-otp", {
        method: "POST",
        body: JSON.stringify({ phone, otp, purpose: "login" }),
      }),

    me: () => request<User>("/auth/me"),

    logout: (refresh_token: string) =>
      request<void>("/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token }) }),
  },

  vehicles: {
    browse: (params: BrowseParams = {}): Promise<PaginatedVehicles> =>
      request(`/vehicles${buildQuery(params as Record<string, unknown>)}`),

    detail: (id: string): Promise<VehicleDetail> => request(`/vehicles/${id}`),
  },

  bookings: {
    preview: (data: { vehicle_id: string; pickup_time: string; dropoff_time: string }): Promise<PricingBreakdown> =>
      request("/bookings/preview", { method: "POST", body: JSON.stringify(data) }),

    create: (data: { vehicle_id: string; pickup_time: string; dropoff_time: string }) =>
      request<Booking>("/bookings", { method: "POST", body: JSON.stringify(data) }),

    list: () => request<Booking[]>("/bookings"),

    cancel: (id: string, reason: string) =>
      request<Booking>(`/bookings/${id}/cancel`, { method: "POST", body: JSON.stringify({ reason }) }),
  },

  owner: {
    cars: (): Promise<OwnerVehicle[]> => request("/owner/cars"),

    createCar: (data: Record<string, unknown>) =>
      request<OwnerVehicle>("/owner/cars", { method: "POST", body: JSON.stringify(data) }),

    updateCar: (id: string, data: Record<string, unknown>) =>
      request<OwnerVehicle>(`/owner/cars/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

    deleteCar: (id: string) => request<void>(`/owner/cars/${id}`, { method: "DELETE" }),

    submitForReview: (id: string) =>
      request<OwnerVehicle>(`/owner/cars/${id}/submit`, { method: "POST" }),

    bookings: () => request<Record<string, unknown>[]>("/owner/bookings"),

    earnings: () => request<EarningsSummary>("/owner/earnings"),

    monthlyEarnings: () => request<MonthlyEarning[]>("/owner/earnings/monthly"),

    blockSlot: (data: { vehicle_id: string; start_time: string; end_time: string; reason: string }) =>
      request("/owner/availability", { method: "POST", body: JSON.stringify(data) }),

    unblockSlot: (slotId: string) =>
      request<void>(`/owner/availability/${slotId}`, { method: "DELETE" }),
  },
};

// ── Formatters ────────────────────────────────────────────────────────────────

export function formatRupees(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function fuelLabel(f: string) {
  return { petrol: "Petrol", diesel: "Diesel", electric: "Electric", hybrid: "Hybrid", cng: "CNG" }[f] ?? f;
}

export function transmissionLabel(t: string) {
  return t === "automatic" ? "Automatic" : "Manual";
}
