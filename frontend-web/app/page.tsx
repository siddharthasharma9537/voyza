"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Navbar from "@/components/Navbar";

const CITIES = ["Hyderabad", "Bangalore", "Mumbai", "Delhi", "Chennai", "Pune"];

export default function HomePage() {
  const router = useRouter();
  const [city, setCity] = useState("");
  const [pickup, setPickup] = useState("");
  const [dropoff, setDropoff] = useState("");

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
          <div className="bg-white rounded-2xl shadow-2xl p-4 sm:p-6 max-w-3xl mx-auto text-left">
            <div className="grid sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">City</label>
                <select
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="">Any city</option>
                  {CITIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Pick-up</label>
                <input
                  type="datetime-local"
                  value={pickup}
                  onChange={(e) => setPickup(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Drop-off</label>
                <input
                  type="datetime-local"
                  value={dropoff}
                  onChange={(e) => setDropoff(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
            </div>

            <button
              onClick={search}
              className="mt-4 w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 rounded-xl transition-colors"
            >
              Search Cars
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
