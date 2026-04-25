"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { api, formatRupees } from "@/lib/api";
import { getStoredUser } from "@/lib/auth";
import type { Booking } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  confirmed: "bg-blue-100 text-blue-700",
  active: "bg-green-100 text-green-700",
  completed: "bg-slate-100 text-slate-600",
  cancelled: "bg-red-100 text-red-600",
};

export default function BookingsDashboard() {
  const router = useRouter();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancelId, setCancelId] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    const user = getStoredUser();
    if (!user) { router.push("/auth/login"); return; }
    api.bookings.list()
      .then(setBookings)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [router]);

  async function cancelBooking() {
    if (!cancelId) return;
    setCancelling(true);
    try {
      const updated = await api.bookings.cancel(cancelId, cancelReason || "Customer requested cancellation");
      setBookings((prev) => prev.map((b) => (b.id === cancelId ? updated : b)));
      setCancelId(null);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Cancellation failed");
    } finally { setCancelling(false); }
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />

      <div className="max-w-4xl mx-auto px-4 py-8 w-full">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">My Bookings</h1>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => <div key={i} className="h-32 bg-slate-200 rounded-2xl animate-pulse" />)}
          </div>
        ) : bookings.length === 0 ? (
          <div className="text-center py-24 text-slate-500">
            <div className="text-5xl mb-4">📋</div>
            <p className="text-lg font-medium">No bookings yet</p>
            <button onClick={() => router.push("/cars")}
              className="mt-4 bg-sky-600 text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-sky-700">
              Browse cars
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {bookings.map((b) => (
              <div key={b.id} className="bg-white border border-slate-200 rounded-2xl p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full capitalize ${STATUS_COLORS[b.status] ?? "bg-slate-100 text-slate-600"}`}>
                        {b.status}
                      </span>
                      <span className="text-xs text-slate-400">#{b.id.slice(0, 8)}</span>
                    </div>

                    <div className="text-sm text-slate-600 mt-2 space-y-0.5">
                      <p>
                        <span className="font-medium text-slate-700">Pick-up:</span>{" "}
                        {new Date(b.pickup_time).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}
                      </p>
                      <p>
                        <span className="font-medium text-slate-700">Drop-off:</span>{" "}
                        {new Date(b.dropoff_time).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}
                      </p>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <p className="text-lg font-bold text-slate-900">{formatRupees(b.total_amount)}</p>
                    {["pending", "confirmed"].includes(b.status) && (
                      <button onClick={() => { setCancelId(b.id); setCancelReason(""); }}
                        className="text-xs text-red-600 hover:underline mt-2">
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Cancel modal */}
      {cancelId && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl">
            <h3 className="font-bold text-slate-900 mb-2">Cancel booking?</h3>
            <p className="text-sm text-slate-500 mb-4">This action cannot be undone.</p>
            <textarea value={cancelReason} onChange={(e) => setCancelReason(e.target.value)}
              placeholder="Reason (optional)"
              rows={2}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-sky-500" />
            <div className="flex gap-3">
              <button onClick={() => setCancelId(null)}
                className="flex-1 border border-slate-200 rounded-lg py-2 text-sm font-medium hover:bg-slate-50">
                Keep booking
              </button>
              <button onClick={cancelBooking} disabled={cancelling}
                className="flex-1 bg-red-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-red-700 disabled:opacity-40">
                {cancelling ? "Cancelling…" : "Yes, cancel"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
