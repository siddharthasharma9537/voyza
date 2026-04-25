"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { api, formatRupees, fuelLabel, transmissionLabel } from "@/lib/api";
import { getStoredUser } from "@/lib/auth";
import type { VehicleDetail, PricingBreakdown } from "@/lib/api";

export default function CarDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [vehicle, setVehicle] = useState<VehicleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [pickup, setPickup] = useState("");
  const [dropoff, setDropoff] = useState("");
  const [preview, setPreview] = useState<PricingBreakdown | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState("");
  const [activeImage, setActiveImage] = useState(0);

  useEffect(() => {
    api.vehicles.detail(id)
      .then(setVehicle)
      .catch(() => setError("Car not found or not available."))
      .finally(() => setLoading(false));
  }, [id]);

  async function getPreview() {
    if (!pickup || !dropoff) return;
    setPreviewLoading(true);
    try {
      const p = await api.bookings.preview({
        vehicle_id: id,
        pickup_time: new Date(pickup).toISOString(),
        dropoff_time: new Date(dropoff).toISOString(),
      });
      setPreview(p);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to get price";
      setBookingError(msg);
    } finally {
      setPreviewLoading(false);
    }
  }

  async function book() {
    const user = getStoredUser();
    if (!user) { router.push("/auth/login"); return; }

    setBookingLoading(true);
    setBookingError("");
    try {
      const booking = await api.bookings.create({
        vehicle_id: id,
        pickup_time: new Date(pickup).toISOString(),
        dropoff_time: new Date(dropoff).toISOString(),
      });
      router.push(`/dashboard/bookings?highlight=${booking.id}`);
    } catch (e: unknown) {
      setBookingError(e instanceof Error ? e.message : "Booking failed");
    } finally {
      setBookingLoading(false);
    }
  }

  if (loading) return <PageShell><div className="animate-pulse h-96 bg-slate-100 rounded-2xl" /></PageShell>;
  if (error || !vehicle) return <PageShell><p className="text-red-600">{error || "Not found"}</p></PageShell>;

  const images = vehicle.images.sort((a, b) => a.sort_order - b.sort_order);
  const currentImg = images[activeImage];

  return (
    <PageShell>
      <div className="max-w-6xl mx-auto px-4 py-8 grid lg:grid-cols-5 gap-8">
        {/* Left: images + details */}
        <div className="lg:col-span-3 space-y-6">
          {/* Image gallery */}
          <div className="rounded-2xl overflow-hidden bg-slate-100 h-72 sm:h-96 relative">
            {currentImg ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={currentImg.url} alt={`${vehicle.make} ${vehicle.model}`}
                className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-300 text-6xl">🚗</div>
            )}
          </div>
          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-1">
              {images.map((img, i) => (
                <button key={img.id} onClick={() => setActiveImage(i)}
                  className={`shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition-colors ${i === activeImage ? "border-sky-500" : "border-transparent"}`}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={img.url} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}

          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              {vehicle.make} {vehicle.model} {vehicle.variant ?? ""}
            </h1>
            <p className="text-slate-500 mt-1">{vehicle.year} · {vehicle.color} · {vehicle.city}, {vehicle.state}</p>
          </div>

          {/* Specs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: "Fuel", value: fuelLabel(vehicle.fuel_type) },
              { label: "Transmission", value: transmissionLabel(vehicle.transmission) },
              { label: "Seating", value: `${vehicle.seating} seats` },
              { label: "Mileage", value: vehicle.mileage_kmpl ? `${vehicle.mileage_kmpl} km/l` : "—" },
            ].map((s) => (
              <div key={s.label} className="bg-slate-50 rounded-xl p-3 text-center">
                <p className="text-xs text-slate-500">{s.label}</p>
                <p className="font-semibold text-slate-900 mt-0.5">{s.value}</p>
              </div>
            ))}
          </div>

          {/* Features */}
          {Object.keys(vehicle.features).length > 0 && (
            <div>
              <h3 className="font-semibold text-slate-900 mb-3">Features</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(vehicle.features)
                  .filter(([, v]) => v)
                  .map(([k]) => (
                    <span key={k} className="text-sm bg-sky-50 text-sky-700 px-3 py-1 rounded-full border border-sky-100">
                      {k.replace(/_/g, " ")}
                    </span>
                  ))}
              </div>
            </div>
          )}

          {vehicle.address && (
            <div>
              <h3 className="font-semibold text-slate-900 mb-1">Pickup location</h3>
              <p className="text-slate-600 text-sm">{vehicle.address}</p>
            </div>
          )}
        </div>

        {/* Right: booking widget */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 sticky top-24 shadow-sm">
            <div className="flex items-baseline gap-2 mb-6">
              <span className="text-2xl font-bold text-slate-900">{formatRupees(vehicle.price_per_day)}</span>
              <span className="text-slate-500">/day</span>
              <span className="text-slate-400 text-sm ml-2">{formatRupees(vehicle.price_per_hour)}/hr</span>
            </div>

            <div className="space-y-3 mb-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Pick-up</label>
                <input type="datetime-local" value={pickup} onChange={(e) => setPickup(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Drop-off</label>
                <input type="datetime-local" value={dropoff} onChange={(e) => setDropoff(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
              </div>
            </div>

            <button onClick={getPreview} disabled={!pickup || !dropoff || previewLoading}
              className="w-full border border-sky-600 text-sky-600 rounded-lg py-2.5 text-sm font-semibold hover:bg-sky-50 disabled:opacity-40 mb-3">
              {previewLoading ? "Calculating…" : "Check price"}
            </button>

            {preview && (
              <div className="bg-slate-50 rounded-xl p-4 mb-4 space-y-1.5 text-sm">
                <Row label="Base" value={formatRupees(preview.base_amount)} />
                {preview.discount_amount > 0 && <Row label="Discount" value={`−${formatRupees(preview.discount_amount)}`} className="text-green-600" />}
                <Row label="Tax" value={formatRupees(preview.tax_amount)} />
                <Row label="Security deposit" value={formatRupees(preview.security_deposit)} />
                <hr className="border-slate-200" />
                <Row label="Total" value={formatRupees(preview.total_amount)} className="font-bold text-slate-900" />
              </div>
            )}

            {bookingError && (
              <p className="text-red-600 text-sm mb-3">{bookingError}</p>
            )}

            <button onClick={book} disabled={!pickup || !dropoff || bookingLoading}
              className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 rounded-xl transition-colors disabled:opacity-40">
              {bookingLoading ? "Booking…" : "Book now"}
            </button>

            <p className="text-xs text-slate-400 text-center mt-3">
              Security deposit of {formatRupees(vehicle.security_deposit)} refunded after trip
            </p>
          </div>
        </div>
      </div>
    </PageShell>
  );
}

function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Row({ label, value, className = "text-slate-700" }: { label: string; value: string; className?: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-500">{label}</span>
      <span className={className}>{value}</span>
    </div>
  );
}
