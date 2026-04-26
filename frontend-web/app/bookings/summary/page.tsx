"use client";

import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

interface BookingSummary {
  id: string;
  booking_reference: string;
  vehicle_name: string;
  vehicle_image: string | null;
  owner_name: string;
  owner_rating: number | null;
  pickup_time: string;
  dropoff_time: string;
  pickup_address: string | null;
  dropoff_address: string | null;
  base_amount: number;
  discount_amount: number;
  tax_amount: number;
  security_deposit: number;
  total_amount: number;
  status: string;
}

export default function BookingSummaryPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookingId = searchParams.get("id");

  const [booking, setBooking] = useState<BookingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!bookingId) {
      setError("Booking not found");
      setLoading(false);
      return;
    }

    fetchBookingDetails();
  }, [bookingId]);

  async function fetchBookingDetails() {
    try {
      const response = await api.bookings.getDetails(bookingId!);
      setBooking(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load booking");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full"></div>
          <p className="mt-4 text-slate-600">Loading your booking...</p>
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 max-w-sm w-full text-center">
          <h1 className="text-xl font-bold text-red-600 mb-2">Error</h1>
          <p className="text-slate-600 mb-6">{error}</p>
          <Link href="/" className="text-sky-600 hover:underline">
            Back to home
          </Link>
        </div>
      </div>
    );
  }

  const pickupDate = new Date(booking.pickup_time);
  const dropoffDate = new Date(booking.dropoff_time);
  const durationHours = (dropoffDate.getTime() - pickupDate.getTime()) / (1000 * 60 * 60);
  const durationDays = Math.ceil(durationHours / 24);

  const amountInRupees = (paise: number) => (paise / 100).toFixed(2);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-500 to-green-600 text-white py-6 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="text-3xl font-bold mb-2">✓ Booking Confirmed!</h1>
          <p className="text-lg opacity-90">Your reference: {booking.booking_reference}</p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Confirmation Message */}
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-8">
          <p className="text-green-900 font-medium">
            ✓ Confirmation details have been sent to your email and phone
          </p>
        </div>

        {/* Vehicle Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-6">
          <div className="grid grid-cols-2 gap-4 p-6">
            {booking.vehicle_image && (
              <img
                src={booking.vehicle_image}
                alt={booking.vehicle_name}
                className="col-span-2 w-full h-48 object-cover rounded-lg"
              />
            )}
            <div className="col-span-2">
              <h2 className="text-2xl font-bold text-slate-900 mb-1">{booking.vehicle_name}</h2>
              <div className="flex items-center gap-2 text-slate-600 mb-2">
                <span>👤 {booking.owner_name}</span>
                {booking.owner_rating && (
                  <span className="ml-2">⭐ {booking.owner_rating.toFixed(1)}</span>
                )}
              </div>
            </div>
          </div>
        </div>


        {/* Pickup & Dropoff */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Pickup */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">📍 Pickup</h3>
            <p className="font-semibold text-slate-900 mb-1">
              {pickupDate.toLocaleDateString("en-IN", { weekday: "short", month: "short", day: "numeric" })}
            </p>
            <p className="text-sm text-slate-600 mb-3">
              {pickupDate.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
            </p>
            {booking.pickup_address && (
              <p className="text-xs text-slate-600 line-clamp-2">{booking.pickup_address}</p>
            )}
          </div>

          {/* Dropoff */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">📍 Dropoff</h3>
            <p className="font-semibold text-slate-900 mb-1">
              {dropoffDate.toLocaleDateString("en-IN", { weekday: "short", month: "short", day: "numeric" })}
            </p>
            <p className="text-sm text-slate-600 mb-3">
              {dropoffDate.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
            </p>
            {booking.dropoff_address && (
              <p className="text-xs text-slate-600 line-clamp-2">{booking.dropoff_address}</p>
            )}
          </div>
        </div>

        {/* Duration */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-center">
          <p className="text-sm text-blue-900 font-medium">
            Duration: {durationDays} {durationDays === 1 ? "day" : "days"} ({durationHours.toFixed(1)} hours)
          </p>
        </div>

        {/* Pricing Breakdown */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <h3 className="text-lg font-bold text-slate-900 mb-4">💰 Pricing Breakdown</h3>

          <div className="space-y-3 mb-4">
            {/* Base Rental */}
            <div className="flex justify-between py-2 border-b border-slate-200">
              <span className="text-slate-600">Base Rental ({durationDays} {durationDays === 1 ? "day" : "days"})</span>
              <span className="font-semibold text-slate-900">₹{amountInRupees(booking.base_amount)}</span>
            </div>

            {/* Discount */}
            {booking.discount_amount > 0 && (
              <div className="flex justify-between py-2 border-b border-slate-200">
                <span className="text-slate-600">Discount</span>
                <span className="font-semibold text-green-600">-₹{amountInRupees(booking.discount_amount)}</span>
              </div>
            )}

            {/* Tax */}
            <div className="flex justify-between py-2 border-b border-slate-200">
              <span className="text-slate-600">Tax (GST)</span>
              <span className="font-semibold text-slate-900">₹{amountInRupees(booking.tax_amount)}</span>
            </div>

            {/* Security Deposit */}
            <div className="flex justify-between py-2 border-b border-slate-200 bg-amber-50 px-3 rounded-lg">
              <span className="text-slate-600">Security Deposit (Refundable)</span>
              <span className="font-semibold text-amber-900">₹{amountInRupees(booking.security_deposit)}</span>
            </div>
          </div>

          {/* Total */}
          <div className="bg-gradient-to-r from-sky-50 to-blue-50 rounded-lg p-4 mb-4">
            <div className="flex justify-between items-center">
              <span className="text-lg font-bold text-sky-900">TOTAL AMOUNT PAID</span>
              <span className="text-3xl font-bold text-sky-600">₹{amountInRupees(booking.total_amount)}</span>
            </div>
          </div>

          <p className="text-xs text-slate-500 text-center italic">
            🛡️ Security deposit will be refunded within 5-7 business days after vehicle return
          </p>
        </div>

        {/* Important Information */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <h3 className="text-lg font-bold text-slate-900 mb-4">ℹ️ Important Information</h3>

          <ul className="space-y-2 text-sm text-slate-700">
            <li className="flex gap-2">
              <span className="text-lg">✓</span>
              <span>Bring your valid Driving License and ID proof</span>
            </li>
            <li className="flex gap-2">
              <span className="text-lg">✓</span>
              <span>You will receive SMS reminders 24 hours and 2 hours before pickup</span>
            </li>
            <li className="flex gap-2">
              <span className="text-lg">✓</span>
              <span>Insurance coverage is included in your booking</span>
            </li>
            <li className="flex gap-2">
              <span className="text-lg">✓</span>
              <span>Fuel policy: Return with the same fuel level as pickup</span>
            </li>
            <li className="flex gap-2">
              <span className="text-lg">✓</span>
              <span>Check vehicle condition at pickup and report any issues immediately</span>
            </li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-8">
          <button
            onClick={() => router.push(`/bookings/${bookingId}`)}
            className="flex-1 bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            View Full Details
          </button>
          <button
            onClick={() => router.push("/")}
            className="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-900 font-semibold py-3 rounded-xl transition-colors"
          >
            Back to Home
          </button>
        </div>

        {/* Support */}
        <div className="text-center text-sm text-slate-600 bg-slate-50 rounded-lg p-4">
          <p className="mb-1">Need help?</p>
          <p>
            <span className="font-medium">support@voyza.com</span>
            {" | "}
            <span className="font-medium">+91-98765-43210</span>
          </p>
        </div>
      </div>
    </div>
  );
}
