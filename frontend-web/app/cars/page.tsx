"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import VehicleCard from "@/components/VehicleCard";
import { api } from "@/lib/api";
import type { VehicleListItem } from "@/lib/api";

const FUEL_TYPES = ["petrol", "diesel", "electric", "hybrid", "cng"];
const TRANSMISSIONS = ["manual", "automatic"];
const CITIES = ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai", "Pune"];

function CarsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [vehicles, setVehicles] = useState<VehicleListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [city, setCity] = useState(searchParams.get("city") ?? "");
  const [fuel, setFuel] = useState(searchParams.get("fuel_type") ?? "");
  const [transmission, setTransmission] = useState(searchParams.get("transmission") ?? "");
  const [maxPrice, setMaxPrice] = useState(searchParams.get("max_price_day") ?? "");
  const [sortBy, setSortBy] = useState<string>(searchParams.get("sort_by") ?? "newest");

  async function fetchVehicles(p = 1) {
    setLoading(true);
    setError("");
    try {
      const res = await api.vehicles.browse({
        city: city || undefined,
        fuel_type: fuel || undefined,
        transmission: transmission || undefined,
        max_price_day: maxPrice ? Number(maxPrice) : undefined,
        sort_by: sortBy as "price_asc" | "price_desc" | "rating" | "newest",
        page: p,
        limit: 12,
      });
      setVehicles(res.items);
      setTotal(res.total);
      setPage(res.page);
      setTotalPages(res.total_pages);
    } catch {
      setError("Failed to load cars. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchVehicles(1); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function applyFilters() {
    const params = new URLSearchParams();
    if (city) params.set("city", city);
    if (fuel) params.set("fuel_type", fuel);
    if (transmission) params.set("transmission", transmission);
    if (maxPrice) params.set("max_price_day", maxPrice);
    params.set("sort_by", sortBy);
    router.push(`/cars?${params.toString()}`);
    fetchVehicles(1);
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 py-8 w-full flex gap-8">
        {/* Sidebar filters */}
        <aside className="w-56 shrink-0 hidden lg:block">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 sticky top-24">
            <h2 className="font-semibold text-slate-900 mb-4">Filters</h2>

            <FilterSection label="City">
              <select
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
              >
                <option value="">All cities</option>
                {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </FilterSection>

            <FilterSection label="Fuel">
              <div className="space-y-1">
                {FUEL_TYPES.map((f) => (
                  <label key={f} className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="radio"
                      name="fuel"
                      value={f}
                      checked={fuel === f}
                      onChange={(e) => setFuel(e.target.value)}
                      className="accent-sky-600"
                    />
                    <span className="capitalize">{f}</span>
                  </label>
                ))}
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="radio" name="fuel" value="" checked={fuel === ""} onChange={() => setFuel("")} className="accent-sky-600" />
                  <span>Any</span>
                </label>
              </div>
            </FilterSection>

            <FilterSection label="Transmission">
              {TRANSMISSIONS.map((t) => (
                <label key={t} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    name="trans"
                    value={t}
                    checked={transmission === t}
                    onChange={(e) => setTransmission(e.target.value)}
                    className="accent-sky-600"
                  />
                  <span className="capitalize">{t}</span>
                </label>
              ))}
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="radio" name="trans" value="" checked={transmission === ""} onChange={() => setTransmission("")} className="accent-sky-600" />
                <span>Any</span>
              </label>
            </FilterSection>

            <FilterSection label="Max price/day (₹)">
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="e.g. 2000"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
              />
            </FilterSection>

            <button
              onClick={applyFilters}
              className="w-full bg-sky-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-sky-700 mt-4"
            >
              Apply
            </button>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-6">
            <p className="text-slate-600 text-sm">
              {loading ? "Loading..." : `${total} cars found`}
            </p>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
            >
              <option value="newest">Newest</option>
              <option value="price_asc">Price: Low → High</option>
              <option value="price_desc">Price: High → Low</option>
              <option value="rating">Best rated</option>
            </select>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4 mb-6 text-sm">{error}</div>
          )}

          {loading ? (
            <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-72 bg-slate-200 rounded-2xl animate-pulse" />
              ))}
            </div>
          ) : vehicles.length === 0 ? (
            <div className="text-center py-24 text-slate-500">
              <div className="text-5xl mb-4">🚗</div>
              <p className="text-lg font-medium">No cars available</p>
              <p className="text-sm mt-1">Try adjusting your filters</p>
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-6">
              {vehicles.map((v) => <VehicleCard key={v.id} v={v} />)}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-10">
              <button
                disabled={page <= 1}
                onClick={() => fetchVehicles(page - 1)}
                className="px-4 py-2 text-sm border rounded-lg disabled:opacity-40 hover:bg-slate-50"
              >
                Previous
              </button>
              <span className="text-sm text-slate-600">Page {page} of {totalPages}</span>
              <button
                disabled={page >= totalPages}
                onClick={() => fetchVehicles(page + 1)}
                className="px-4 py-2 text-sm border rounded-lg disabled:opacity-40 hover:bg-slate-50"
              >
                Next
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function FilterSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">{label}</p>
      {children}
    </div>
  );
}

export default function CarsPage() {
  return (
    <Suspense>
      <CarsContent />
    </Suspense>
  );
}
