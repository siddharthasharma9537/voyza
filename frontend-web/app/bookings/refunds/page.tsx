"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Refund {
  id: string;
  booking_reference: string;
  booking_id: string;
  vehicle_name: string;
  cancellation_date: string;
  refund_amount: number;
  status: "pending" | "initiated" | "processed" | "failed";
  expected_date: string;
  created_at: string;
}

export default function RefundsPage() {
  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchRefunds();
  }, []);

  async function fetchRefunds() {
    try {
      // Mock data for demo
      const mockRefunds: Refund[] = [
        {
          id: "ref1",
          booking_reference: "VOY-20260425-001",
          booking_id: "booking1",
          vehicle_name: "Maruti Swift",
          cancellation_date: "2026-04-25T10:30:00Z",
          refund_amount: 791400,
          status: "processed",
          expected_date: "2026-04-28T00:00:00Z",
          created_at: "2026-04-25T10:30:00Z",
        },
        {
          id: "ref2",
          booking_reference: "VOY-20260424-002",
          booking_id: "booking2",
          vehicle_name: "Hyundai i20",
          cancellation_date: "2026-04-24T14:15:00Z",
          refund_amount: 437800,
          status: "initiated",
          expected_date: "2026-04-29T00:00:00Z",
          created_at: "2026-04-24T14:15:00Z",
        },
        {
          id: "ref3",
          booking_reference: "VOY-20260423-003",
          booking_id: "booking3",
          vehicle_name: "Tata Nexon",
          cancellation_date: "2026-04-23T09:00:00Z",
          refund_amount: 649500,
          status: "pending",
          expected_date: "2026-04-30T00:00:00Z",
          created_at: "2026-04-23T09:00:00Z",
        },
      ];
      setRefunds(mockRefunds);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load refunds");
    } finally {
      setLoading(false);
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "processed":
        return "bg-green-100 text-green-800 border-green-300";
      case "initiated":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "failed":
        return "bg-red-100 text-red-800 border-red-300";
      default:
        return "bg-slate-100 text-slate-800 border-slate-300";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "processed":
        return "✓ Refunded";
      case "initiated":
        return "⏳ In Progress";
      case "pending":
        return "⏳ Pending";
      case "failed":
        return "✕ Failed";
      default:
        return "?";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processed":
        return "✓";
      case "initiated":
        return "⏳";
      case "pending":
        return "⏳";
      case "failed":
        return "✕";
      default:
        return "•";
    }
  };

  const amountInRupees = (paise: number) => (paise / 100).toFixed(2);

  const processedCount = refunds.filter((r) => r.status === "processed").length;
  const processingCount = refunds.filter((r) => r.status === "initiated" || r.status === "pending").length;
  const totalRefundAmount = refunds.reduce((sum, r) => sum + r.refund_amount, 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-8 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full"></div>
          <p className="mt-4 text-slate-600">Loading refund information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">💰 Refunds</h1>
          <p className="text-slate-600">Track your booking cancellations and refunds</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <p className="text-sm text-slate-600 mb-2">Total Refunded</p>
            <p className="text-2xl font-bold text-green-600">₹{amountInRupees(totalRefundAmount)}</p>
            <p className="text-xs text-slate-500 mt-1">{processedCount} completed</p>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <p className="text-sm text-slate-600 mb-2">In Progress</p>
            <p className="text-2xl font-bold text-blue-600">{processingCount}</p>
            <p className="text-xs text-slate-500 mt-1">Processing your refund</p>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <p className="text-sm text-slate-600 mb-2">Total Cancellations</p>
            <p className="text-2xl font-bold text-slate-900">{refunds.length}</p>
            <p className="text-xs text-slate-500 mt-1">Bookings cancelled</p>
          </div>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
          <p className="text-sm text-blue-900 mb-1">
            <strong>ℹ️ Refund Timeline:</strong>
          </p>
          <p className="text-sm text-blue-800">
            Most refunds are processed within <strong>5-7 business days</strong> after cancellation. For failed refunds, please contact our support team.
          </p>
        </div>

        {/* Refunds List */}
        {refunds.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12 text-center">
            <p className="text-slate-600 text-lg mb-2">No refunds yet</p>
            <p className="text-slate-500 text-sm">You haven't cancelled any bookings</p>
          </div>
        ) : (
          <div className="space-y-4">
            {refunds.map((refund) => {
              const cancellationDate = new Date(refund.cancellation_date);
              const expectedDate = new Date(refund.expected_date);
              const isProcessed = refund.status === "processed";

              return (
                <div key={refund.id} className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow p-6">
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div>
                      <h3 className="font-bold text-slate-900">{refund.vehicle_name}</h3>
                      <p className="text-sm text-slate-600">Booking: {refund.booking_reference}</p>
                    </div>
                    <div className={`rounded-lg border px-3 py-1 text-sm font-medium whitespace-nowrap ${getStatusColor(refund.status)}`}>
                      {getStatusBadge(refund.status)}
                    </div>
                  </div>

                  {/* Refund Progress Timeline */}
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">📅</span>
                          <div>
                            <p className="text-xs text-slate-600">Cancellation Date</p>
                            <p className="font-semibold text-slate-900">
                              {cancellationDate.toLocaleDateString("en-IN", {
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="text-2xl">→</div>

                      <div className="flex-1 text-right">
                        <div className="flex items-center justify-end gap-2 mb-2">
                          <div>
                            <p className="text-xs text-slate-600">Expected Refund</p>
                            <p className="font-semibold text-slate-900">
                              {expectedDate.toLocaleDateString("en-IN", {
                                month: "short",
                                day: "numeric",
                              })}
                            </p>
                          </div>
                          <span className="text-lg">✓</span>
                        </div>
                      </div>
                    </div>

                    {/* Status Progress */}
                    <div className="space-y-2">
                      {/* Pending */}
                      <div className="flex items-center gap-3">
                        <span className="text-lg">{refund.status === "pending" ? "⏳" : "✓"}</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900">Refund Initiated</p>
                          <p className="text-xs text-slate-600">Your refund request received</p>
                        </div>
                      </div>

                      {/* Initiated */}
                      <div className="flex items-center gap-3">
                        <span className={`text-lg ${["initiated", "processed"].includes(refund.status) ? "✓" : "○"}`}>
                          {["initiated", "processed"].includes(refund.status) ? "✓" : "◯"}
                        </span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900">Processing</p>
                          <p className="text-xs text-slate-600">Bank is processing your refund</p>
                        </div>
                      </div>

                      {/* Processed */}
                      <div className="flex items-center gap-3">
                        <span className={`text-lg ${isProcessed ? "✓" : "○"}`}>
                          {isProcessed ? "✓" : "◯"}
                        </span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900">Refunded</p>
                          <p className="text-xs text-slate-600">Money credited to your account</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Refund Amount */}
                  <div className="bg-green-50 rounded-lg p-4">
                    <p className="text-sm text-green-900 mb-1">Refund Amount</p>
                    <p className="text-2xl font-bold text-green-900">₹{amountInRupees(refund.refund_amount)}</p>
                  </div>

                  {/* Action for Failed */}
                  {refund.status === "failed" && (
                    <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="text-sm text-red-900 font-medium mb-3">Refund Failed</p>
                      <button className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 rounded-lg transition-colors">
                        Contact Support
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-6">
            <p className="text-red-900 font-medium">Error loading refunds</p>
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {/* Support Section */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <p className="text-sm text-blue-900 mb-3">
            <strong>Questions about your refund?</strong>
          </p>
          <p className="text-sm text-blue-800 mb-4">
            Contact our support team for assistance
          </p>
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
            Contact Support
          </button>
        </div>
      </div>
    </div>
  );
}
