"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import VaadinDateTimePicker from "@/components/VaadinDateTimePicker";
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

  // Auto-populate drop-off when pick-up is set, or fix if invalid
  useEffect(() => {
    if (pickup) {
      const pickupDate = new Date(pickup);

      if (!dropoff) {
        // Set drop-off to next day at same time
        const dropoffDate = new Date(pickupDate);
        dropoffDate.setDate(dropoffDate.getDate() + 1);
        setDropoff(dropoffDate.toISOString());
      } else {
        // Check if drop-off is before or equal to pick-up, and auto-correct
        const dropoffDate = new Date(dropoff);
        if (dropoffDate <= pickupDate) {
          // Auto-set drop-off to next day
          const correctedDropoff = new Date(pickupDate);
          correctedDropoff.setDate(correctedDropoff.getDate() + 1);
          setDropoff(correctedDropoff.toISOString());
        }
      }
    }
  }, [pickup]);

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
          <div className="bg-gradient-to-b from-white to-slate-50 border-2 border-sky-200 rounded-3xl p-5 sm:p-8 sticky top-20 sm:top-24 shadow-xl">
            {/* Price Header - Eye catching */}
            <div className="bg-gradient-to-r from-sky-50 to-indigo-50 p-4 rounded-2xl mb-6 border border-sky-300">
              <span className="text-xs text-sky-700 font-bold uppercase tracking-wide block mb-2">Starting price</span>
              <div className="flex items-end justify-between">
                <span className="text-4xl font-bold text-sky-900">{formatRupees(vehicle.price_per_day)}</span>
                <div className="text-right">
                  <span className="text-sky-700 block text-sm font-semibold">/day</span>
                  <span className="text-xs text-sky-600 font-medium">{formatRupees(vehicle.price_per_hour)}/hr</span>
                </div>
              </div>
            </div>

            <div className="space-y-3 mb-6">
              <VaadinDateTimePicker label="Pick-up" value={pickup} onChange={setPickup} />
              <VaadinDateTimePicker
                label="Drop-off"
                value={dropoff}
                onChange={setDropoff}
                showTomorrow
                minDateTime={pickup}
              />
            </div>

            {!preview && pickup && dropoff && (
              <button onClick={getPreview} disabled={previewLoading}
                className="w-full border border-sky-600 text-sky-600 rounded-lg py-2.5 text-sm font-semibold hover:bg-sky-50 disabled:opacity-40 mb-3 transition-colors">
                {previewLoading ? "Calculating…" : "Calculate total price"}
              </button>
            )}

            {preview && (
              <div className="bg-gradient-to-br from-emerald-50 via-blue-50 to-purple-50 rounded-2xl p-5 mb-5 space-y-2.5 text-sm border-2 border-emerald-300 shadow-md">
                <div className="flex justify-between items-center pb-3 border-b-2 border-emerald-300 bg-white/50 p-3 rounded-lg">
                  <span className="text-slate-700 font-semibold">📅 Duration</span>
                  <span className="font-bold text-emerald-700 text-base">
                    {preview.duration_days > 0
                      ? `${preview.duration_days}d ${preview.duration_hours % 24}h`
                      : `${preview.duration_hours}h`}
                  </span>
                </div>
                <div className="space-y-2 bg-white/40 p-3 rounded-lg">
                  <Row label="Base fare" value={formatRupees(preview.base_amount)} />
                  {preview.discount_amount > 0 && <Row label="💰 Discount" value={`−${formatRupees(preview.discount_amount)}`} className="text-green-600 font-bold text-base" />}
                  <Row label="Tax & fees" value={formatRupees(preview.tax_amount)} />
                </div>
                <div className="bg-white/60 p-3 rounded-lg border-l-4 border-sky-500">
                  <div className="text-xs text-slate-600 mb-1.5">🔒 Security deposit (refunded)</div>
                  <span className="text-slate-600 text-xs">{formatRupees(preview.security_deposit)}</span>
                </div>
                <div className="bg-gradient-to-r from-sky-600 to-indigo-600 rounded-xl p-4 mt-3">
                  <div className="text-white/90 text-xs font-medium mb-1">💳 Total amount to pay</div>
                  <div className="text-3xl font-bold text-white">{formatRupees(preview.total_amount)}</div>
                </div>
              </div>
            )}

            {bookingError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-700">
                {bookingError}
              </div>
            )}

            <button onClick={book} disabled={!pickup || !dropoff || bookingLoading}
              className="w-full bg-sky-600 hover:bg-sky-700 disabled:bg-slate-300 text-white font-semibold py-3 rounded-xl transition-all disabled:opacity-60 disabled:cursor-not-allowed mb-3">
              {bookingLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⏳</span> Confirming booking…
                </span>
              ) : (
                "Confirm booking"
              )}
            </button>

            <p className="text-xs text-slate-500 text-center space-y-1">
              <div>Security deposit: {formatRupees(vehicle.security_deposit)}</div>
              <div className="text-slate-400">Refunded after trip completion</div>
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
