"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import VaadinDateTimePicker from "@/components/VaadinDateTimePicker";

const CITIES = ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai", "Pune"];

export default function HomePage() {
  const router = useRouter();
  const [city, setCity] = useState("");
  const [pickup, setPickup] = useState("");
  const [dropoff, setDropoff] = useState("");

  // Auto-correct drop-off if it becomes invalid
  useEffect(() => {
    if (pickup) {
      const pickupDate = new Date(pickup);
      if (dropoff) {
        const dropoffDate = new Date(dropoff);
        if (dropoffDate <= pickupDate) {
          // Auto-set drop-off to next day
          const correctedDropoff = new Date(pickupDate);
          correctedDropoff.setDate(correctedDropoff.getDate() + 1);
          setDropoff(correctedDropoff.toISOString());
        }
      } else {
        // Auto-populate drop-off if empty
        const dropoffDate = new Date(pickupDate);
        dropoffDate.setDate(dropoffDate.getDate() + 1);
        setDropoff(dropoffDate.toISOString());
      }
    }
  }, [pickup]);

  function search() {
    const params = new URLSearchParams();
    if (city) params.set("city", city);
    if (pickup) params.set("pickup_time", new Date(pickup).toISOString());
    if (dropoff) params.set("dropoff_time", new Date(dropoff).toISOString());
    router.push(`/cars?${params.toString()}`);
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Hero */}
      <section className="flex-1 bg-gradient-to-br from-sky-600 via-sky-500 to-indigo-600 text-white">
        <div className="max-w-5xl mx-auto px-4 py-24 text-center">
          <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight mb-4">
            Drive on your terms
          </h1>
          <p className="text-xl text-sky-100 mb-12 max-w-2xl mx-auto">
            Rent cars from verified local owners. Affordable daily rates, no hidden fees.
          </p>

          {/* Search bar */}
          <div className="bg-gradient-to-br from-white via-blue-50 to-indigo-50 rounded-3xl shadow-2xl p-6 sm:p-10 max-w-4xl mx-auto text-left border-2 border-sky-300">
            <h2 className="text-2xl font-bold text-sky-900 mb-2">🚗 Book your ride</h2>
            <p className="text-slate-600 text-sm mb-6">Find the perfect car for your journey</p>

            <div className="grid sm:grid-cols-4 gap-4 mb-6">
              <div>
                <label className="block text-xs font-bold text-sky-700 mb-2 uppercase tracking-wide">📍 City</label>
                <select
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="w-full border-2 border-sky-300 rounded-xl px-3 py-3 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-sky-600 font-semibold bg-white hover:border-sky-400"
                >
                  <option value="">Select city</option>
                  {CITIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div className="sm:col-span-1.5">
                <VaadinDateTimePicker label="📅 Pick-up" value={pickup} onChange={setPickup} />
              </div>
              <div className="sm:col-span-1.5">
                <VaadinDateTimePicker
                  label="📅 Drop-off"
                  value={dropoff}
                  onChange={setDropoff}
                  showTomorrow
                  minDateTime={pickup}
                />
              </div>
            </div>

            {/* Helper text */}
            {city && pickup && dropoff && (
              <div className="flex items-center gap-3 text-base font-semibold text-white mb-6 bg-gradient-to-r from-emerald-500 to-green-500 p-4 rounded-xl border-2 border-emerald-400 shadow-md">
                <span className="text-2xl">✅</span>
                <span>Ready to search for {CITIES.includes(city) ? city : 'any'} cars</span>
              </div>
            )}

            <button
              onClick={search}
              disabled={!city || !pickup || !dropoff}
              className="w-full bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 disabled:from-slate-400 disabled:to-slate-400 text-white font-bold py-4 rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-lg shadow-lg border-2 border-sky-400"
            >
              {city && pickup && dropoff ? "🔍 Search available cars" : "⬆️ Select all fields above"}
            </button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-white">
        <div className="max-w-5xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-slate-900 mb-12">Why Voyza?</h2>
          <div className="grid sm:grid-cols-3 gap-8">
            {[
              { icon: "🛡️", title: "Verified owners", desc: "Every car owner goes through KYC verification before listing." },
              { icon: "💳", title: "Secure payments", desc: "Razorpay-powered checkout. Security deposit returned after every trip." },
              { icon: "🕐", title: "Flexible timing", desc: "Rent by the hour or by the day. Pickup and drop wherever you need." },
            ].map((f) => (
              <div key={f.title} className="text-center p-6">
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="font-semibold text-slate-900 text-lg mb-2">{f.title}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-slate-900 text-white py-16 text-center">
        <h2 className="text-3xl font-bold mb-4">Own a car? Earn from it.</h2>
        <p className="text-slate-400 mb-8 max-w-md mx-auto">
          List your car in minutes and start earning. You set the price, we handle the rest.
        </p>
        <Link
          href="/auth/register?role=owner"
          className="inline-block bg-sky-500 hover:bg-sky-400 text-white font-semibold px-8 py-3 rounded-xl transition-colors"
        >
          List your car →
        </Link>
      </section>

      <footer className="bg-slate-950 text-slate-500 text-sm text-center py-6">
        © {new Date().getFullYear()} Voyza. All rights reserved.
      </footer>
    </div>
  );
}
