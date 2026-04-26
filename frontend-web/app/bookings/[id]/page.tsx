"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { PickupLocationMap } from "@/components/PickupLocationMap";

interface BookingDetail {
  id: string;
  booking_reference: string;
  status: string;
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
  cancel_reason: string | null;
  cancelled_at: string | null;
  created_at: string;
}

export default function ManageBookingPage() {
  const params = useParams();
  const router = useRouter();
  const bookingId = params.id as string;

  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancelling, setCancelling] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [showCancelModal, setShowCancelModal] = useState(false);

  useEffect(() => {
    fetchBookingDetails();
  }, [bookingId]);

  async function fetchBookingDetails() {
    try {
      const response = await api.bookings.getDetails(bookingId);
      setBooking(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load booking");
    } finally {
      setLoading(false);
    }
  }

  async function handleCancelBooking() {
    if (!cancelReason.trim()) {
      alert("Please provide a reason for cancellation");
      return;
    }

    setCancelling(true);
    try {
      await api.bookings.cancel(bookingId, cancelReason);
      setShowCancelModal(false);
      // Refresh booking details
      await fetchBookingDetails();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to cancel booking");
    } finally {
      setCancelling(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full"></div>
          <p className="mt-4 text-slate-600">Loading booking...</p>
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
          <button
            onClick={() => router.push("/")}
            className="text-sky-600 hover:underline font-medium"
          >
            Back to home
          </button>
        </div>
      </div>
    );
  }

  const pickupDate = new Date(booking.pickup_time);
  const dropoffDate = new Date(booking.dropoff_time);
  const isUpcoming = new Date() < pickupDate;
  const isCompleted = booking.status === "completed";
  const isCancelled = booking.status === "cancelled";

  const amountInRupees = (paise: number) => (paise / 100).toFixed(2);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "confirmed":
        return "bg-green-100 text-green-800 border-green-300";
      case "active":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "completed":
        return "bg-slate-100 text-slate-800 border-slate-300";
      case "cancelled":
        return "bg-red-100 text-red-800 border-red-300";
      default:
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "confirmed":
        return "✓ Confirmed";
      case "active":
        return "🚗 Active";
      case "completed":
        return "✓ Completed";
      case "cancelled":
        return "✕ Cancelled";
      default:
        return "⏳ Pending";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <button
            onClick={() => router.back()}
            className="text-sky-600 hover:text-sky-700 font-medium flex items-center gap-1"
          >
            ← Back
          </button>
          <div className="text-right">
            <h1 className="text-2xl font-bold text-slate-900">Booking Details</h1>
            <p className="text-sm text-slate-500">{booking.booking_reference}</p>
          </div>
        </div>

        {/* Status Badge */}
        <div className={`rounded-lg border px-4 py-3 mb-6 font-medium text-center ${getStatusColor(booking.status)}`}>
          {getStatusBadge(booking.status)}
        </div>

        {/* Cancellation Info */}
        {isCancelled && booking.cancel_reason && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-red-900">
              <strong>Cancellation Reason:</strong> {booking.cancel_reason}
            </p>
            <p className="text-xs text-red-800 mt-1">
              Cancelled on {new Date(booking.cancelled_at!).toLocaleDateString()}
            </p>
          </div>
        )}

        {/* Vehicle Section */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">🚗 Vehicle</h2>

          <div className="flex gap-4">
            {booking.vehicle_image && (
              <img
                src={booking.vehicle_image}
                alt={booking.vehicle_name}
                className="w-24 h-24 rounded-lg object-cover"
              />
            )}
            <div className="flex-1">
              <h3 className="text-xl font-bold text-slate-900">{booking.vehicle_name}</h3>
              <p className="text-slate-600 text-sm mb-2">
                Owner: <span className="font-medium">{booking.owner_name}</span>
                {booking.owner_rating && (
                  <span className="ml-2">
                    ⭐ {booking.owner_rating.toFixed(1)}
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Pickup Location Map */}
        {isUpcoming && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">🗺️ Pickup Location</h2>
            <PickupLocationMap
              latitude={booking.pickup_latitude || "0"}
              longitude={booking.pickup_longitude || "0"}
              address={booking.pickup_address}
              vehicleName={booking.vehicle_name}
            />
          </div>
        )}

        {/* Pickup & Dropoff */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
              <span className="text-lg">📍</span> Pickup
            </h3>
            <p className="text-sm text-slate-600 mb-1">Date & Time</p>
            <p className="font-semibold text-slate-900 mb-3">
              {pickupDate.toLocaleDateString("en-IN", {
                weekday: "short",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
            {booking.pickup_address && (
              <>
                <p className="text-sm text-slate-600 mb-1">Location</p>
                <p className="text-sm font-medium text-slate-900">{booking.pickup_address}</p>
              </>
            )}
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
              <span className="text-lg">📍</span> Dropoff
            </h3>
            <p className="text-sm text-slate-600 mb-1">Date & Time</p>
            <p className="font-semibold text-slate-900 mb-3">
              {dropoffDate.toLocaleDateString("en-IN", {
                weekday: "short",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
            {booking.dropoff_address && (
              <>
                <p className="text-sm text-slate-600 mb-1">Location</p>
                <p className="text-sm font-medium text-slate-900">{booking.dropoff_address}</p>
              </>
            )}
          </div>
        </div>

        {/* Pricing Details */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">💰 Pricing</h2>

          <div className="space-y-2 mb-4">
            <div className="flex justify-between py-2 border-b border-slate-200">
              <span className="text-slate-600">Base Amount</span>
              <span className="font-semibold">₹{amountInRupees(booking.base_amount)}</span>
            </div>
            {booking.discount_amount > 0 && (
              <div className="flex justify-between py-2 border-b border-slate-200">
                <span className="text-slate-600">Discount</span>
                <span className="font-semibold text-green-600">-₹{amountInRupees(booking.discount_amount)}</span>
              </div>
            )}
            <div className="flex justify-between py-2 border-b border-slate-200">
              <span className="text-slate-600">Tax (GST)</span>
              <span className="font-semibold">₹{amountInRupees(booking.tax_amount)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-200 bg-amber-50 px-3 rounded">
              <span className="text-slate-600">Security Deposit (Refundable)</span>
              <span className="font-semibold">₹{amountInRupees(booking.security_deposit)}</span>
            </div>
          </div>

          <div className="bg-sky-50 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <span className="font-bold text-slate-900">Total Amount</span>
              <span className="text-2xl font-bold text-sky-600">₹{amountInRupees(booking.total_amount)}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        {isUpcoming && !isCancelled && (
          <div className="flex gap-3 mb-6">
            <button
              onClick={() => setShowCancelModal(true)}
              className="flex-1 bg-red-100 hover:bg-red-200 text-red-700 font-semibold py-3 rounded-xl transition-colors"
            >
              Cancel Booking
            </button>
          </div>
        )}

        {/* Contact Support */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <p className="text-sm text-blue-900 mb-2">Need help managing your booking?</p>
          <p className="text-xs text-blue-800">
            Contact our support team: <span className="font-medium">support@voyza.com</span>
          </p>
        </div>
      </div>

      {/* Cancel Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center px-4 z-50">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-lg p-6 max-w-sm w-full">
            <h2 className="text-xl font-bold text-slate-900 mb-4">Cancel Booking?</h2>

            <p className="text-slate-600 mb-4 text-sm">
              Are you sure you want to cancel this booking? You'll receive a refund within 5-7 business days.
            </p>

            <textarea
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="Please tell us why you're cancelling..."
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 mb-4 resize-none h-24"
            />

            <div className="flex gap-3">
              <button
                onClick={() => setShowCancelModal(false)}
                disabled={cancelling}
                className="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-900 font-semibold py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                Keep Booking
              </button>
              <button
                onClick={handleCancelBooking}
                disabled={cancelling || !cancelReason.trim()}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                {cancelling ? "Cancelling..." : "Confirm Cancel"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
