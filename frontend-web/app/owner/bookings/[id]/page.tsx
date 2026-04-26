"use client";

import { useParams, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface OwnerBookingDetail {
  id: string;
  booking_reference: string;
  status: string;
  vehicle_name: string;
  vehicle_image: string | null;
  customer_name: string;
  customer_phone: string;
  customer_email: string | null;
  pickup_time: string;
  dropoff_time: string;
  pickup_address: string | null;
  dropoff_address: string | null;
  total_amount: number;
  owner_earnings: number;
  created_at: string;
}

interface ChecklistItem {
  id: string;
  label: string;
  completed: boolean;
  required: boolean;
}

export default function OwnerBookingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const bookingId = params.id as string;

  const [booking, setBooking] = useState<OwnerBookingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [pickupChecklist, setPickupChecklist] = useState<ChecklistItem[]>([
    { id: "fuel", label: "Fill fuel to full tank", completed: false, required: true },
    { id: "wash", label: "Wash and clean vehicle", completed: false, required: true },
    { id: "interior", label: "Clean interior (seats, floor, dashboard)", completed: false, required: true },
    { id: "documents", label: "Prepare RC, insurance, key, spare key", completed: false, required: true },
    { id: "photos", label: "Take vehicle condition photos", completed: false, required: true },
    { id: "odometer", label: "Note current odometer reading", completed: false, required: true },
    { id: "inspect", label: "Inspect for dents, scratches, damage", completed: false, required: true },
  ]);

  const [returnChecklist, setReturnChecklist] = useState<ChecklistItem[]>([
    { id: "fuel-return", label: "Check fuel level (should be full)", completed: false, required: true },
    { id: "condition", label: "Check vehicle condition for damage", completed: false, required: true },
    { id: "mileage", label: "Record odometer reading", completed: false, required: true },
    { id: "interior-return", label: "Inspect interior condition", completed: false, required: true },
    { id: "photos-return", label: "Take return condition photos", completed: false, required: true },
    { id: "documents-return", label: "Collect all documents back", completed: false, required: true },
  ]);

  const [showPhotoUpload, setShowPhotoUpload] = useState(false);
  const [uploadedPhotos, setUploadedPhotos] = useState<string[]>([]);

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

  function toggleChecklistItem(list: ChecklistItem[], index: number, setter: (items: ChecklistItem[]) => void) {
    const updated = [...list];
    updated[index].completed = !updated[index].completed;
    setter(updated);
  }

  const allPickupCompleted = pickupChecklist.filter((i) => i.required).every((i) => i.completed);
  const allReturnCompleted = returnChecklist.filter((i) => i.required).every((i) => i.completed);

  const pickupCompletedCount = pickupChecklist.filter((i) => i.completed).length;
  const returnCompletedCount = returnChecklist.filter((i) => i.completed).length;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full"></div>
          <p className="mt-4 text-slate-600">Loading booking details...</p>
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
            onClick={() => router.back()}
            className="text-sky-600 hover:underline font-medium"
          >
            Go back
          </button>
        </div>
      </div>
    );
  }

  const pickupDate = new Date(booking.pickup_time);
  const dropoffDate = new Date(booking.dropoff_time);
  const isUpcoming = new Date() < pickupDate;
  const isActive = booking.status === "active";
  const isCompleted = booking.status === "completed";

  const amountInRupees = (paise: number) => (paise / 100).toFixed(0);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <button
            onClick={() => router.back()}
            className="text-sky-600 hover:text-sky-700 font-medium flex items-center gap-1"
          >
            ← Back to Bookings
          </button>
          <div className="text-right">
            <h1 className="text-2xl font-bold text-slate-900">Booking Details</h1>
            <p className="text-sm text-slate-500">{booking.booking_reference}</p>
          </div>
        </div>

        {/* Booking Info Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase mb-4">📋 Booking Details</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-slate-600">Vehicle</p>
                  <p className="font-semibold text-slate-900">{booking.vehicle_name}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Customer</p>
                  <p className="font-semibold text-slate-900">{booking.customer_name}</p>
                  <p className="text-sm text-slate-600">{booking.customer_phone}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Status</p>
                  <p className="font-semibold text-slate-900">
                    {booking.status === "active" ? "🚗 Active" : isUpcoming ? "⏳ Confirmed" : "✓ Completed"}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase mb-4">🕐 Schedule</h3>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-slate-600">Pickup</p>
                  <p className="font-semibold text-slate-900">
                    {pickupDate.toLocaleDateString("en-IN", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Dropoff</p>
                  <p className="font-semibold text-slate-900">
                    {dropoffDate.toLocaleDateString("en-IN", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase mb-4">💰 Earnings</h3>
              <div className="bg-green-50 rounded-lg p-3">
                <p className="text-xs text-green-600 mb-1">Your Earnings</p>
                <p className="text-2xl font-bold text-green-900">₹{amountInRupees(booking.owner_earnings)}</p>
                <p className="text-xs text-green-700 mt-1">Total booking: ₹{amountInRupees(booking.total_amount)}</p>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase mb-4">📍 Locations</h3>
              <div className="space-y-2 text-sm">
                {booking.pickup_address && (
                  <div>
                    <p className="text-slate-600">Pickup:</p>
                    <p className="font-medium text-slate-900">{booking.pickup_address}</p>
                  </div>
                )}
                {booking.dropoff_address && (
                  <div>
                    <p className="text-slate-600">Dropoff:</p>
                    <p className="font-medium text-slate-900">{booking.dropoff_address}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Pre-Pickup Checklist */}
        {isUpcoming && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900">✅ Pre-Pickup Checklist</h2>
              <div className="text-sm font-medium text-slate-600">
                {pickupCompletedCount}/{pickupChecklist.length} Done
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-200 rounded-full h-2 mb-4">
              <div
                className="bg-green-500 h-2 rounded-full transition-all"
                style={{ width: `${(pickupCompletedCount / pickupChecklist.length) * 100}%` }}
              ></div>
            </div>

            {/* Checklist Items */}
            <div className="space-y-2">
              {pickupChecklist.map((item, index) => (
                <label
                  key={item.id}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={item.completed}
                    onChange={() => toggleChecklistItem(pickupChecklist, index, setPickupChecklist)}
                    className="w-5 h-5 accent-green-600 cursor-pointer"
                  />
                  <div className="flex-1">
                    <p className={`font-medium ${item.completed ? "text-slate-500 line-through" : "text-slate-900"}`}>
                      {item.label}
                    </p>
                  </div>
                  {item.required && <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">Required</span>}
                </label>
              ))}
            </div>

            {/* Ready Button */}
            {allPickupCompleted && (
              <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-green-900 font-semibold">✓ You're ready for pickup!</p>
                <p className="text-sm text-green-700">Vehicle is prepared. Customer can be picked up.</p>
              </div>
            )}
          </div>
        )}

        {/* Active Rental - Return Checklist */}
        {isActive && (
          <div className="bg-white rounded-2xl border border-blue-200 shadow-sm p-6 mb-6 border-l-4 border-l-blue-600">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900">🚗 Vehicle Currently Rented</h2>
              <div className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
                Dropoff in {Math.ceil((dropoffDate.getTime() - new Date().getTime()) / (1000 * 60 * 60))} hours
              </div>
            </div>

            <p className="text-slate-600 mb-4">
              Customer has the vehicle. Get ready for return pickup and inspection.
            </p>

            <div className="bg-blue-50 rounded-lg p-4 mb-4">
              <p className="text-sm text-blue-900 font-medium">Expected Dropoff Time</p>
              <p className="text-lg font-bold text-blue-900">
                {dropoffDate.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })} on{" "}
                {dropoffDate.toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
              </p>
            </div>
          </div>
        )}

        {/* Post-Return Checklist */}
        {isCompleted && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900">✓ Vehicle Returned</h2>
              <div className="text-sm font-medium text-slate-600">
                {returnCompletedCount}/{returnChecklist.length} Verified
              </div>
            </div>

            <div className="w-full bg-slate-200 rounded-full h-2 mb-4">
              <div
                className="bg-green-500 h-2 rounded-full transition-all"
                style={{ width: `${(returnCompletedCount / returnChecklist.length) * 100}%` }}
              ></div>
            </div>

            <div className="space-y-2">
              {returnChecklist.map((item, index) => (
                <label
                  key={item.id}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={item.completed}
                    onChange={() => toggleChecklistItem(returnChecklist, index, setReturnChecklist)}
                    className="w-5 h-5 accent-green-600 cursor-pointer"
                  />
                  <div className="flex-1">
                    <p className={`font-medium ${item.completed ? "text-slate-500 line-through" : "text-slate-900"}`}>
                      {item.label}
                    </p>
                  </div>
                  {item.required && <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">Required</span>}
                </label>
              ))}
            </div>

            {/* Photo Upload */}
            <div className="mt-4 p-4 border-2 border-dashed border-slate-300 rounded-lg">
              <button
                onClick={() => setShowPhotoUpload(!showPhotoUpload)}
                className="text-sky-600 hover:text-sky-700 font-medium flex items-center gap-2"
              >
                📸 {uploadedPhotos.length > 0 ? `${uploadedPhotos.length} photo(s) uploaded` : "Upload condition photos"}
              </button>
            </div>

            {allReturnCompleted && (
              <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-green-900 font-semibold">✓ Return verified!</p>
                <p className="text-sm text-green-700">Earnings transferred to your account.</p>
              </div>
            )}
          </div>
        )}

        {/* Customer Contact */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-900 mb-2">
            <strong>Need to reach customer?</strong>
          </p>
          <div className="flex gap-2">
            <a
              href={`tel:${booking.customer_phone}`}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-center font-medium transition-colors"
            >
              📞 Call
            </a>
            {booking.customer_email && (
              <a
                href={`mailto:${booking.customer_email}`}
                className="flex-1 bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-2 rounded-lg text-center font-medium transition-colors"
              >
                ✉️ Email
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
