"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { api, formatRupees } from "@/lib/api";
import { getStoredUser } from "@/lib/auth";
import type { OwnerVehicle, EarningsSummary, MonthlyEarning } from "@/lib/api";

type Tab = "cars" | "earnings" | "bookings";

export default function OwnerDashboard() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("cars");
  const [cars, setCars] = useState<OwnerVehicle[]>([]);
  const [earnings, setEarnings] = useState<EarningsSummary | null>(null);
  const [monthly, setMonthly] = useState<MonthlyEarning[]>([]);
  const [bookings, setBookings] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddCar, setShowAddCar] = useState(false);

  useEffect(() => {
    const user = getStoredUser();
    if (!user) { router.push("/auth/login"); return; }
    if (user.role !== "owner") { router.push("/dashboard/bookings"); return; }

    Promise.all([
      api.owner.cars(),
      api.owner.earnings(),
      api.owner.monthlyEarnings(),
      api.owner.bookings(),
    ]).then(([c, e, m, b]) => {
      setCars(c);
      setEarnings(e);
      setMonthly(m);
      setBookings(b);
    }).finally(() => setLoading(false));
  }, [router]);

  async function deleteCar(id: string) {
    if (!confirm("Delete this car?")) return;
    await api.owner.deleteCar(id);
    setCars((prev) => prev.filter((c) => c.id !== id));
  }

  async function submitForReview(id: string) {
    try {
      const updated = await api.owner.submitForReview(id);
      setCars((prev) => prev.map((c) => (c.id === id ? { ...c, status: updated.status } : c)));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Submission failed");
    }
  }

  if (loading) return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-8 w-full">
        <div className="h-12 w-48 bg-slate-200 rounded-xl animate-pulse mb-8" />
        <div className="grid sm:grid-cols-3 gap-4 mb-8">
          {[1,2,3].map(i => <div key={i} className="h-28 bg-slate-200 rounded-2xl animate-pulse" />)}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />

      <div className="max-w-5xl mx-auto px-4 py-8 w-full">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-slate-900">Owner Dashboard</h1>
          {tab === "cars" && (
            <button onClick={() => setShowAddCar(true)}
              className="bg-sky-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-sky-700">
              + Add car
            </button>
          )}
        </div>

        {/* Summary cards */}
        {earnings && (
          <div className="grid sm:grid-cols-4 gap-4 mb-8">
            <StatCard label="Total earnings" value={formatRupees(earnings.total_earnings)} />
            <StatCard label="This month" value={formatRupees(earnings.this_month)} />
            <StatCard label="Pending payout" value={formatRupees(earnings.pending_payout)} />
            <StatCard label="Total bookings" value={String(earnings.total_bookings)} />
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-100 rounded-xl p-1 mb-6 w-fit">
          {(["cars", "earnings", "bookings"] as Tab[]).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium capitalize transition-colors ${tab === t ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
              {t}
            </button>
          ))}
        </div>

        {/* Cars tab */}
        {tab === "cars" && (
          <div className="space-y-4">
            {cars.length === 0 && (
              <div className="text-center py-16 text-slate-500">
                <div className="text-5xl mb-3">🚗</div>
                <p>No cars listed yet. Add your first car!</p>
              </div>
            )}
            {cars.map((car) => (
              <div key={car.id} className="bg-white border border-slate-200 rounded-2xl p-5 flex gap-4">
                <div className="w-24 h-16 rounded-xl overflow-hidden bg-slate-100 shrink-0">
                  {car.images?.[0] ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={car.images[0].url} alt="" className="w-full h-full object-cover" />
                  ) : <div className="w-full h-full flex items-center justify-center text-2xl">🚗</div>}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold text-slate-900">{car.make} {car.model} ({car.year})</p>
                      <p className="text-sm text-slate-500">{car.registration_number} · {car.city}</p>
                    </div>
                    <div className="flex gap-1.5 shrink-0">
                      <StatusBadge status={car.status} />
                      <KycBadge status={car.kyc_status} />
                    </div>
                  </div>

                  <div className="flex items-center gap-4 mt-3">
                    <span className="text-sm text-slate-600">{formatRupees(car.price_per_day)}/day</span>
                    {car.status === "draft" && (
                      <button onClick={() => submitForReview(car.id)}
                        className="text-xs bg-sky-50 text-sky-700 border border-sky-200 px-3 py-1 rounded-lg hover:bg-sky-100 font-medium">
                        Submit for review
                      </button>
                    )}
                    <button onClick={() => deleteCar(car.id)}
                      className="text-xs text-red-500 hover:text-red-700 ml-auto">
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Earnings tab */}
        {tab === "earnings" && (
          <div>
            {monthly.length === 0 ? (
              <p className="text-slate-500 text-center py-16">No earnings data yet.</p>
            ) : (
              <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Month</th>
                      <th className="text-right px-5 py-3 font-semibold text-slate-600">Bookings</th>
                      <th className="text-right px-5 py-3 font-semibold text-slate-600">Earnings</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {monthly.map((m) => (
                      <tr key={m.month} className="hover:bg-slate-50">
                        <td className="px-5 py-3 text-slate-700">{m.month}</td>
                        <td className="px-5 py-3 text-right text-slate-600">{m.bookings}</td>
                        <td className="px-5 py-3 text-right font-semibold text-slate-900">{formatRupees(m.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Bookings tab */}
        {tab === "bookings" && (
          <div>
            {bookings.length === 0 ? (
              <p className="text-slate-500 text-center py-16">No bookings for your cars yet.</p>
            ) : (
              <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Car</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Customer</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Dates</th>
                      <th className="text-right px-5 py-3 font-semibold text-slate-600">Status</th>
                      <th className="text-right px-5 py-3 font-semibold text-slate-600">Earnings</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {bookings.map((b) => (
                      <tr key={String(b.id)} className="hover:bg-slate-50">
                        <td className="px-5 py-3 text-slate-700">{String(b.vehicle_make ?? "")} {String(b.vehicle_model ?? "")}</td>
                        <td className="px-5 py-3 text-slate-600">{String(b.customer_name ?? "")}</td>
                        <td className="px-5 py-3 text-slate-600 text-xs">
                          {new Date(String(b.pickup_time)).toLocaleDateString("en-IN")} →{" "}
                          {new Date(String(b.dropoff_time)).toLocaleDateString("en-IN")}
                        </td>
                        <td className="px-5 py-3 text-right">
                          <span className="text-xs capitalize bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                            {String(b.status)}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-right font-semibold text-slate-900">
                          {formatRupees(Number(b.owner_earnings ?? 0))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Add car modal */}
      {showAddCar && (
        <AddCarModal
          onClose={() => setShowAddCar(false)}
          onCreated={(car) => { setCars((prev) => [car, ...prev]); setShowAddCar(false); }}
        />
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4">
      <p className="text-xs text-slate-500 font-medium">{label}</p>
      <p className="text-xl font-bold text-slate-900 mt-1">{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: "bg-slate-100 text-slate-600",
    pending: "bg-amber-100 text-amber-700",
    active: "bg-green-100 text-green-700",
    suspended: "bg-red-100 text-red-600",
  };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${colors[status] ?? "bg-slate-100 text-slate-600"}`}>
      {status}
    </span>
  );
}

function KycBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    approved: "bg-emerald-100 text-emerald-700",
    rejected: "bg-red-100 text-red-600",
  };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors[status] ?? "bg-slate-100 text-slate-600"}`}>
      KYC: {status}
    </span>
  );
}

function AddCarModal({ onClose, onCreated }: { onClose: () => void; onCreated: (car: OwnerVehicle) => void }) {
  const [form, setForm] = useState({
    make: "", model: "", variant: "", year: new Date().getFullYear(),
    color: "", seating: 5, fuel_type: "petrol", transmission: "manual",
    city: "", state: "", price_per_hour: 100, price_per_day: 800,
    security_deposit: 3000, registration_number: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function set(key: string, value: unknown) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit() {
    setLoading(true); setError("");
    try {
      const car = await api.owner.createCar({ ...form, features: {} });
      onCreated(car as OwnerVehicle);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create car");
    } finally { setLoading(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl p-6 w-full max-w-lg shadow-xl my-4">
        <h3 className="font-bold text-slate-900 text-lg mb-5">Add new car</h3>

        <div className="grid sm:grid-cols-2 gap-3 mb-3">
          {[
            { key: "make", label: "Make", placeholder: "Toyota" },
            { key: "model", label: "Model", placeholder: "Innova" },
            { key: "variant", label: "Variant", placeholder: "Crysta (optional)" },
            { key: "color", label: "Color", placeholder: "White" },
            { key: "city", label: "City", placeholder: "Hyderabad" },
            { key: "state", label: "State", placeholder: "Telangana" },
            { key: "registration_number", label: "Reg. number", placeholder: "TS09AB1234" },
          ].map(({ key, label, placeholder }) => (
            <div key={key}>
              <label className="block text-xs font-semibold text-slate-500 mb-1">{label}</label>
              <input value={String((form as Record<string, unknown>)[key] ?? "")}
                onChange={(e) => set(key, e.target.value)}
                placeholder={placeholder}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
            </div>
          ))}

          {[
            { key: "year", label: "Year", type: "number" },
            { key: "seating", label: "Seats", type: "number" },
            { key: "price_per_hour", label: "Price/hour (₹)", type: "number" },
            { key: "price_per_day", label: "Price/day (₹)", type: "number" },
            { key: "security_deposit", label: "Security deposit (₹)", type: "number" },
          ].map(({ key, label }) => (
            <div key={key}>
              <label className="block text-xs font-semibold text-slate-500 mb-1">{label}</label>
              <input type="number" value={Number((form as Record<string, unknown>)[key])}
                onChange={(e) => set(key, Number(e.target.value))}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
            </div>
          ))}

          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Fuel</label>
            <select value={form.fuel_type} onChange={(e) => set("fuel_type", e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm">
              {["petrol", "diesel", "electric", "hybrid", "cng"].map((f) => (
                <option key={f} value={f} className="capitalize">{f}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Transmission</label>
            <select value={form.transmission} onChange={(e) => set("transmission", e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm">
              <option value="manual">Manual</option>
              <option value="automatic">Automatic</option>
            </select>
          </div>
        </div>

        {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

        <div className="flex gap-3 mt-4">
          <button onClick={onClose}
            className="flex-1 border border-slate-200 rounded-lg py-2.5 text-sm font-medium hover:bg-slate-50">
            Cancel
          </button>
          <button onClick={submit} disabled={loading || !form.make || !form.model || !form.registration_number}
            className="flex-1 bg-sky-600 text-white rounded-lg py-2.5 text-sm font-semibold hover:bg-sky-700 disabled:opacity-40">
            {loading ? "Creating…" : "Create listing"}
          </button>
        </div>
      </div>
    </div>
  );
}
