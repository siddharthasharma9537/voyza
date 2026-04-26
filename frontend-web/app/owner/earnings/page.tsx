"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface EarningsSummary {
  total_earnings: number;
  this_month: number;
  last_month: number;
  pending_payout: number;
  total_bookings: number;
  completed_bookings: number;
  avg_rating: number | null;
  top_car: string | null;
}

interface MonthlyEarning {
  month: string;
  amount: number;
  bookings: number;
}

export default function OwnerEarningsPage() {
  const [earnings, setEarnings] = useState<EarningsSummary | null>(null);
  const [monthlyEarnings, setMonthlyEarnings] = useState<MonthlyEarning[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchEarnings();
  }, []);

  async function fetchEarnings() {
    try {
      const [earningsData, monthlyData] = await Promise.all([
        api.owner.earnings(),
        api.owner.monthlyEarnings(),
      ]);
      setEarnings(earningsData);
      setMonthlyEarnings(monthlyData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load earnings");
    } finally {
      setLoading(false);
    }
  }

  const amountInRupees = (paise: number) => (paise / 100).toFixed(0);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-8 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full"></div>
          <p className="mt-4 text-slate-600">Loading earnings data...</p>
        </div>
      </div>
    );
  }

  if (!earnings) {
    return (
      <div className="min-h-screen bg-slate-50 py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-900 font-medium">Error loading earnings</p>
            <p className="text-red-800 text-sm">{error}</p>
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
          <h1 className="text-3xl font-bold text-slate-900 mb-2">💰 Your Earnings</h1>
          <p className="text-slate-600">Track your rental income and payouts</p>
        </div>

        {/* Main Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* Total Earnings */}
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
            <p className="text-sm text-slate-600 mb-2">Total Earnings</p>
            <p className="text-3xl font-bold text-green-600">₹{amountInRupees(earnings.total_earnings)}</p>
            <p className="text-xs text-slate-500 mt-2">All time</p>
          </div>

          {/* This Month */}
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
            <p className="text-sm text-slate-600 mb-2">This Month</p>
            <p className="text-3xl font-bold text-blue-600">₹{amountInRupees(earnings.this_month)}</p>
            <p className="text-xs text-slate-500 mt-2">Current month</p>
          </div>

          {/* Last Month */}
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
            <p className="text-sm text-slate-600 mb-2">Last Month</p>
            <p className="text-3xl font-bold text-slate-900">₹{amountInRupees(earnings.last_month)}</p>
            <p className="text-xs text-slate-500 mt-2">Previous month</p>
          </div>

          {/* Pending Payout */}
          <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
            <p className="text-sm text-slate-600 mb-2">Pending Payout</p>
            <p className="text-3xl font-bold text-orange-600">₹{amountInRupees(earnings.pending_payout)}</p>
            <p className="text-xs text-slate-500 mt-2">From active bookings</p>
          </div>
        </div>

        {/* Booking Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200 p-6">
            <p className="text-sm text-blue-600 mb-2">Total Bookings</p>
            <p className="text-2xl font-bold text-blue-900">{earnings.total_bookings}</p>
            <p className="text-xs text-blue-700 mt-1">All rentals</p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200 p-6">
            <p className="text-sm text-green-600 mb-2">Completed</p>
            <p className="text-2xl font-bold text-green-900">{earnings.completed_bookings}</p>
            <p className="text-xs text-green-700 mt-1">Successful rentals</p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200 p-6">
            <p className="text-sm text-purple-600 mb-2">Top Vehicle</p>
            <p className="text-lg font-bold text-purple-900 truncate">{earnings.top_car || "—"}</p>
            <p className="text-xs text-purple-700 mt-1">Highest earner</p>
          </div>
        </div>

        {/* Monthly Breakdown */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-8">
          <h2 className="text-lg font-bold text-slate-900 mb-4">📊 Monthly Breakdown</h2>

          {monthlyEarnings.length === 0 ? (
            <p className="text-slate-600 text-center py-8">No earnings data available yet</p>
          ) : (
            <div className="space-y-3">
              {monthlyEarnings.map((month) => (
                <div key={month.month} className="flex items-center justify-between p-4 rounded-lg hover:bg-slate-50 transition-colors border border-slate-100">
                  <div className="flex-1">
                    <p className="font-semibold text-slate-900">{month.month}</p>
                    <p className="text-sm text-slate-600">{month.bookings} bookings</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-green-600">₹{amountInRupees(month.amount)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <p className="text-sm text-blue-900 mb-2">
            <strong>ℹ️ How earnings are calculated:</strong>
          </p>
          <ul className="text-sm text-blue-800 space-y-1 ml-4">
            <li>• Earnings = Base rental amount × (1 - platform fee)</li>
            <li>• Platform fee: 5%</li>
            <li>• Security deposit is NOT included in earnings</li>
            <li>• Earnings credited after booking completion</li>
            <li>• Refunds and cancellations may reduce your earnings</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
