export interface User {
  id: string;
  full_name: string;
  email?: string;
  phone: string;
  role: 'customer' | 'owner';
  is_verified: boolean;
  avatar_url?: string;
}

export interface Vehicle {
  id: string;
  make: string;
  model: string;
  variant?: string;
  year: number;
  city: string;
  fuel_type: string;
  transmission: string;
  seating: number;
  price_per_hour: number;
  price_per_day: number;
  primary_image?: string;
  avg_rating?: number;
  review_count?: number;
  color?: string;
  mileage_kmpl?: number;
  security_deposit: number;
  features?: Record<string, boolean>;
  images?: VehicleImage[];
  status?: string;
}

export interface VehicleImage {
  id: string;
  url: string;
  is_primary: boolean;
  sort_order: number;
}

export interface BookingCreate {
  vehicle_id: string;
  pickup_time: string;
  dropoff_time: string;
  pickup_address?: string;
  pickup_latitude?: number;
  pickup_longitude?: number;
  promo_code?: string;
}

export interface Booking {
  id: string;
  booking_reference?: string;
  vehicle_id: string;
  customer_id: string;
  owner_id?: string;
  pickup_time: string;
  dropoff_time: string;
  pickup_address?: string;
  status: 'pending' | 'confirmed' | 'active' | 'completed' | 'cancelled' | 'disputed';
  base_amount: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  security_deposit: number;
  promo_code?: string;
  car_make?: string;
  car_model?: string;
  car_image?: string;
  created_at?: string;
  cancelled_at?: string;
  cancel_reason?: string;
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

export interface Review {
  id: string;
  booking_id: string;
  vehicle_id: string;
  reviewer: string;
  rating: number;
  comment?: string;
  owner_reply?: string;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface PaginatedVehicles {
  items: Vehicle[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PaymentOrder {
  key_id: string;
  razorpay_order_id: string;
  amount: number;
  currency: string;
}

export type DocumentType = 'driving_license' | 'aadhar' | 'selfie' | 'vehicle_rc' | 'vehicle_insurance';
export type DocumentStatus = 'pending' | 'verified' | 'rejected' | 'expired' | 'requires_resubmission';

export interface KycDocument {
  id: string;
  type: DocumentType;
  status: DocumentStatus;
  rejection_reason?: string;
  uploaded_at?: string;
  verified_at?: string;
}

export interface KycStatus {
  required_types: DocumentType[];
  documents: KycDocument[];
  is_fully_verified: boolean;
}

export interface DamageReport {
  id?: string;
  booking_id: string;
  damage_type: string;
  description: string;
  damage_photos?: string[];
  estimated_cost?: number;
}

export type NavigationParamList = {
  Splash: undefined;
  Login: undefined;
  Register: undefined;
  Main: undefined;
  Home: undefined;
  Browse: { city?: string } | undefined;
  CarDetail: { car: Vehicle };
  Checkout: { car: Vehicle };
  Payment: { booking: Booking; car: Vehicle };
  BookingSuccess: { booking: Booking; car: Vehicle };
  Bookings: undefined;
  Review: { booking: Booking };
  Tracking: { booking: Booking };
  Profile: undefined;
  KycUpload: undefined;
  KycStatus: undefined;
};
