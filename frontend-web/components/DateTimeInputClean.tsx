"use client";

import { useState, useEffect, useRef } from "react";

interface DateTimeInputCleanProps {
  value: string; // ISO 8601 datetime string
  onChange: (value: string) => void;
  label: string;
}

export default function DateTimeInputClean({
  value,
  onChange,
  label,
}: DateTimeInputCleanProps) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("09:00");
  const [isTimeOpen, setIsTimeOpen] = useState(false);
  const timeListRef = useRef<HTMLDivElement>(null);

  // Generate time options (00:00 to 23:00)
  const timeOptions = Array.from({ length: 24 }, (_, i) =>
    `${String(i).padStart(2, "0")}:00`
  );

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

  // Scroll time list to selected time when opened
  useEffect(() => {
    if (isTimeOpen && timeListRef.current) {
      const selectedIndex = timeOptions.findIndex((t) => t === time.substring(0, 5));
      if (selectedIndex !== -1) {
        const scrollTop = selectedIndex * 36 - 72; // 36px per item, offset to center
        setTimeout(() => {
          if (timeListRef.current) {
            timeListRef.current.scrollTop = Math.max(0, scrollTop);
          }
        }, 0);
      }
    }
  }, [isTimeOpen]);

  function handleTimeSelect(selectedTime: string) {
    setTime(selectedTime);
    setIsTimeOpen(false);
  }

  // Handle clicking outside the time picker
  const timePickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (timePickerRef.current && !timePickerRef.current.contains(event.target as Node)) {
        setIsTimeOpen(false);
      }
    }

    if (isTimeOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isTimeOpen]);

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

        {/* Time Picker */}
        <div className="relative" ref={timePickerRef}>
          <button
            onClick={() => setIsTimeOpen(!isTimeOpen)}
            className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-900 bg-white hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 text-left"
          >
            {time}
          </button>

          {/* Time Dropdown */}
          {isTimeOpen && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg z-50">
              <div
                ref={timeListRef}
                className="overflow-y-auto h-64 scroll-smooth"
              >
                {timeOptions.map((timeOption) => (
                  <button
                    key={timeOption}
                    onClick={() => handleTimeSelect(timeOption)}
                    className={`w-full px-3 py-2.5 text-sm text-left transition-colors ${
                      time.substring(0, 5) === timeOption
                        ? "bg-sky-500 text-white font-semibold"
                        : "text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {timeOption}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
