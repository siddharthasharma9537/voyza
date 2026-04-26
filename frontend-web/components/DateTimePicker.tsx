"use client";

import { useState, useEffect } from "react";

interface DateTimePickerProps {
  value: string;
  onChange: (value: string) => void;
  label: string;
  inline?: boolean;
}

export default function DateTimePicker({ value, onChange, label, inline = false }: DateTimePickerProps) {
  const [date, setDate] = useState("");
  const [hour, setHour] = useState("09");
  const [minute, setMinute] = useState("00");
  const [ampm, setAmpm] = useState("AM");

  // Initialize from value (ISO string)
  useEffect(() => {
    if (value) {
      try {
        const dt = new Date(value);
        const dateStr = dt.toISOString().split("T")[0];
        let h = dt.getHours();
        const m = dt.getMinutes();
        const am = h >= 12 ? "PM" : "AM";
        if (h > 12) h -= 12;
        if (h === 0) h = 12;

        setDate(dateStr);
        setHour(String(h).padStart(2, "0"));
        setMinute(String(m).padStart(2, "0"));
        setAmpm(am);
      } catch (e) {
        // Invalid date, set defaults
        const now = new Date();
        setDate(now.toISOString().split("T")[0]);
      }
    } else {
      // Default to today at 9:00 AM
      const now = new Date();
      setDate(now.toISOString().split("T")[0]);
      setHour("09");
      setMinute("00");
      setAmpm("AM");
    }
  }, []);

  // Update the ISO string whenever any field changes
  useEffect(() => {
    if (date) {
      try {
        let h = parseInt(hour, 10);
        if (ampm === "PM" && h !== 12) h += 12;
        if (ampm === "AM" && h === 12) h = 0;

        const dateTime = new Date(`${date}T${String(h).padStart(2, "0")}:${minute}:00`);
        onChange(dateTime.toISOString());
      } catch (e) {
        // Invalid date
      }
    }
  }, [date, hour, minute, ampm, onChange]);

  // Generate hour options (1-12)
  const hours = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, "0"));

  // Generate minute options (00, 15, 30, 45, and all minutes for granularity)
  const minutes = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, "0"));

  if (inline) {
    // Compact inline version for search bar
    return (
      <div>
        <label className="block text-xs font-semibold text-slate-500 mb-1">{label}</label>
        <div className="flex gap-1">
          {/* Date selector */}
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="flex-1 border border-slate-200 rounded-lg px-2 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-sky-500"
          />

          {/* Hour dropdown */}
          <select
            value={hour}
            onChange={(e) => setHour(e.target.value)}
            className="w-14 border border-slate-200 rounded-lg px-1.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
          >
            {hours.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>

          {/* Minute dropdown */}
          <select
            value={minute}
            onChange={(e) => setMinute(e.target.value)}
            className="w-14 border border-slate-200 rounded-lg px-1.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
          >
            {minutes.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>

          {/* AM/PM toggle */}
          <div className="flex border border-slate-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setAmpm("AM")}
              className={`px-2 py-2 text-xs font-medium transition-colors ${
                ampm === "AM"
                  ? "bg-sky-600 text-white"
                  : "bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              AM
            </button>
            <button
              onClick={() => setAmpm("PM")}
              className={`px-2 py-2 text-xs font-medium transition-colors ${
                ampm === "PM"
                  ? "bg-sky-600 text-white"
                  : "bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              PM
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Full vertical version for booking detail page
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-1">{label}</label>
      <div className="space-y-2">
        {/* Date selector */}
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
        />

        {/* Time selectors */}
        <div className="flex gap-2">
          {/* Hour dropdown */}
          <select
            value={hour}
            onChange={(e) => setHour(e.target.value)}
            className="flex-1 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
          >
            {hours.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>

          {/* Minute dropdown */}
          <select
            value={minute}
            onChange={(e) => setMinute(e.target.value)}
            className="flex-1 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
          >
            {minutes.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>

          {/* AM/PM toggle */}
          <div className="flex border border-slate-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setAmpm("AM")}
              className={`flex-1 px-3 py-2.5 text-sm font-medium transition-colors ${
                ampm === "AM"
                  ? "bg-sky-600 text-white"
                  : "bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              AM
            </button>
            <button
              onClick={() => setAmpm("PM")}
              className={`flex-1 px-3 py-2.5 text-sm font-medium transition-colors ${
                ampm === "PM"
                  ? "bg-sky-600 text-white"
                  : "bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              PM
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
