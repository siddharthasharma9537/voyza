export interface User {
  id: string;
  full_name: string;
  email?: string;
  phone: string;
  role: 'customer' | 'owner';
  is_verified: boolean;
  avatar_url?: string;
}

export interface OwnerVehicle {
  id: string;
  make: string;
  model: string;
  variant?: string;
  year: number;
  color: string;
  city: string;
  state?: string;
  registration_number: string;
  fuel_type: string;
  transmission: string;
  seating: number;
  price_per_day: number;
  price_per_hour: number;
  security_deposit: number;
  status: 'draft' | 'pending' | 'active' | 'suspended';
  kyc_status: 'pending' | 'approved' | 'rejected';
  features?: Record<string, boolean>;
  images?: VehicleImage[];
  avg_rating?: number;
  review_count?: number;
}

export interface VehicleImage {
  id: string;
  url: string;
  is_primary: boolean;
}

export interface OwnerBooking {
  id: string;
  booking_reference?: string;
  vehicle_id: string;
  vehicle_make: string;
  vehicle_model: string;
  customer_name: string;
  customer_phone: string;
  pickup_time: string;
  dropoff_time: string;
  status: 'pending' | 'confirmed' | 'active' | 'completed' | 'cancelled';
  total_amount: number;
  owner_earnings: number;
}

export interface BlockedSlot {
  id: string;
  vehicle_id: string;
  start_time: string;
  end_time: string;
  reason: string;
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

export type DocumentType = 'driving_license' | 'aadhar' | 'selfie' | 'vehicle_rc' | 'vehicle_insurance';
export type DocumentStatus = 'pending' | 'verified' | 'rejected' | 'expired' | 'requires_resubmission';

export interface KycDocument {
  id: string;
  type: DocumentType;
  status: DocumentStatus;
}

export type OwnerNavigationParamList = {
  Splash: undefined;
  Login: undefined;
  Register: undefined;
  Main: undefined;
  Dashboard: undefined;
  Cars: undefined;
  AddCar: undefined;
  CarDetail: { car: OwnerVehicle };
  Availability: { carId: string };
  Bookings: undefined;
  BookingDetail: { booking: OwnerBooking };
  Earnings: undefined;
  Profile: undefined;
  KycUpload: undefined;
  KycStatus: undefined;
};
