"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface OwnerBooking {
  id: string;
  booking_reference: string;
  status: string;
  customer_name: string;
  customer_phone: string;
  vehicle_name: string;
  vehicle_image: string | null;
  pickup_time: string;
  dropoff_time: string;
  total_amount: number;
  owner_earnings: number;
  created_at: string;
}

type TabType = "pending" | "active" | "completed" | "cancelled";

export default function OwnerBookingsPage() {
  const [bookings, setBookings] = useState<OwnerBooking[]>([]);
  const [filteredBookings, setFilteredBookings] = useState<OwnerBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<TabType>("pending");

  useEffect(() => {
    fetchBookings();
  }, []);

  useEffect(() => {
    filterBookings(activeTab);
  }, [activeTab, bookings]);

  async function fetchBookings() {
    try {
      const response = await api.owner.bookings();
      setBookings(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load bookings");
    } finally {
      setLoading(false);
    }
  }

  function filterBookings(tab: TabType) {
    const filtered = bookings.filter((b) => {
      if (tab === "pending") return b.status === "pending" || b.status === "confirmed";
      if (tab === "active") return b.status === "active";
      if (tab === "completed") return b.status === "completed";
      if (tab === "cancelled") return b.status === "cancelled";
      return true;
    });
    setFilteredBookings(filtered);
  }

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
        return "⏳ Confirmed";
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

  const amountInRupees = (paise: number) => (paise / 100).toFixed(0);

  const pendingCount = bookings.filter((b) => b.status === "confirmed" || b.status === "pending").length;
  const activeCount = bookings.filter((b) => b.status === "active").length;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center">
            <div className="animate-spin inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full"></div>
            <p className="mt-4 text-slate-600">Loading your bookings...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold text-slate-900">🚗 Your Bookings</h1>
            <button
              onClick={fetchBookings}
              className="bg-sky-600 hover:bg-sky-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              🔄 Refresh
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <p className="text-sm text-slate-600 mb-1">Total Bookings</p>
              <p className="text-2xl font-bold text-slate-900">{bookings.length}</p>
            </div>
            <div className="bg-orange-50 rounded-lg border border-orange-200 p-4">
              <p className="text-sm text-orange-600 mb-1">Pending Pickups</p>
              <p className="text-2xl font-bold text-orange-900">{pendingCount}</p>
            </div>
            <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
              <p className="text-sm text-blue-600 mb-1">Active Rentals</p>
              <p className="text-2xl font-bold text-blue-900">{activeCount}</p>
            </div>
            <div className="bg-green-50 rounded-lg border border-green-200 p-4">
              <p className="text-sm text-green-600 mb-1">Total Earnings</p>
              <p className="text-2xl font-bold text-green-900">
                ₹{amountInRupees(bookings.reduce((sum, b) => sum + (b.owner_earnings || 0), 0))}
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6 flex gap-2 border-b border-slate-200 overflow-x-auto">
          {(["pending", "active", "completed", "cancelled"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 font-medium whitespace-nowrap transition-colors border-b-2 ${
                activeTab === tab
                  ? "border-sky-600 text-sky-600"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              {tab === "pending" && `⏳ Pending (${pendingCount})`}
              {tab === "active" && `🚗 Active (${activeCount})`}
              {tab === "completed" && "✓ Completed"}
              {tab === "cancelled" && "✕ Cancelled"}
            </button>
          ))}
        </div>

        {/* Bookings List */}
        {filteredBookings.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12 text-center">
            <p className="text-slate-600 text-lg mb-2">No bookings in this category</p>
            <p className="text-slate-500 text-sm">Check back later for new rental requests</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredBookings.map((booking) => {
              const pickupDate = new Date(booking.pickup_time);
              const dropoffDate = new Date(booking.dropoff_time);
              const isUpcoming = new Date() < pickupDate;

              return (
                <Link key={booking.id} href={`/owner/bookings/${booking.id}`}>
                  <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow p-4 cursor-pointer">
                    <div className="flex gap-4">
                      {/* Vehicle Image */}
                      {booking.vehicle_image && (
                        <img
                          src={booking.vehicle_image}
                          alt={booking.vehicle_name}
                          className="w-20 h-20 rounded-lg object-cover flex-shrink-0"
                        />
                      )}

                      {/* Details */}
                      <div className="flex-1">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div>
                            <h3 className="font-bold text-slate-900">{booking.vehicle_name}</h3>
                            <p className="text-sm text-slate-600">
                              👤 {booking.customer_name} • {booking.customer_phone}
                            </p>
                          </div>
                          <div className={`rounded-lg border px-3 py-1 text-sm font-medium whitespace-nowrap ${getStatusColor(booking.status)}`}>
                            {getStatusBadge(booking.status)}
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                          <div>
                            <p className="text-slate-600">Pickup</p>
                            <p className="font-semibold text-slate-900">
                              {pickupDate.toLocaleDateString("en-IN", {
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                          </div>
                          <div>
                            <p className="text-slate-600">Dropoff</p>
                            <p className="font-semibold text-slate-900">
                              {dropoffDate.toLocaleDateString("en-IN", {
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <p className="text-xs text-slate-500">
                            Booking: {booking.booking_reference}
                          </p>
                          <div className="flex items-center gap-4">
                            <div>
                              <p className="text-xs text-slate-600">Your Earnings</p>
                              <p className="font-bold text-green-600">₹{amountInRupees(booking.owner_earnings)}</p>
                            </div>
                            {isUpcoming && booking.status !== "cancelled" && (
                              <div className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs font-medium">
                                ⚠️ Action Needed
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-6">
            <p className="text-red-900 font-medium">Error loading bookings</p>
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
