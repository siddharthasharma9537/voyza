"use client";

import { useState, useEffect } from "react";

interface DateTimeInputProps {
  value: string; // ISO 8601 datetime string
  onChange: (value: string) => void;
  label: string;
}

export default function DateTimeInput({
  value,
  onChange,
  label,
}: DateTimeInputProps) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("09:00");

  // Initialize from value
  useEffect(() => {
    if (value) {
      try {
        const dt = new Date(value);
        const dateStr = dt.toISOString().split("T")[0];
        const hours = String(dt.getHours()).padStart(2, "0");
        const minutes = String(dt.getMinutes()).padStart(2, "0");
        const timeStr = `${hours}:${minutes}`;

        setDate(dateStr);
        setTime(timeStr);
      } catch (e) {
        const now = new Date();
        setDate(now.toISOString().split("T")[0]);
      }
    } else {
      const now = new Date();
      setDate(now.toISOString().split("T")[0]);
      setTime("09:00");
    }
  }, []);

  // Update ISO string whenever date or time changes
  useEffect(() => {
    if (date && time) {
      try {
        const dateTime = new Date(`${date}T${time}:00`);
        onChange(dateTime.toISOString());
      } catch (e) {
        // Invalid date
      }
    }
  }, [date, time, onChange]);

  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-2">
        {label}
      </label>
      <div className="space-y-2">
        {/* Date Input */}
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
        />

        {/* Time Input */}
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
        />
      </div>
    </div>
  );
}
