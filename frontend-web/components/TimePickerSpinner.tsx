"use client";

import { useState, useRef, useEffect } from "react";

interface TimePickerSpinnerProps {
  value: string; // ISO 8601 datetime string
  onChange: (value: string) => void;
  label: string;
}

export default function TimePickerSpinner({
  value,
  onChange,
  label,
}: TimePickerSpinnerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [date, setDate] = useState("");
  const [hour, setHour] = useState("09");
  const [minute, setMinute] = useState("00");
  const [ampm, setAmpm] = useState("AM");
  const [displayTime, setDisplayTime] = useState("09:00 AM");

  // Initialize from value
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
        setDisplayTime(`${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")} ${am}`);
      } catch (e) {
        const now = new Date();
        setDate(now.toISOString().split("T")[0]);
      }
    } else {
      const now = new Date();
      setDate(now.toISOString().split("T")[0]);
      setDisplayTime("09:00 AM");
    }
  }, []);

  // Update ISO string
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

  function handleDone() {
    setDisplayTime(`${hour}:${minute} ${ampm}`);
    setIsOpen(false);
  }

  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-2">
        {label}
      </label>

      {/* Date Input */}
      <input
        type="date"
        value={date}
        onChange={(e) => setDate(e.target.value)}
        className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 mb-2"
      />

      {/* Time Display Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="w-full border border-slate-200 rounded-lg px-4 py-2.5 text-sm font-semibold text-slate-900 bg-white hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500"
      >
        {displayTime}
      </button>

      {/* Time Picker Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-end sm:items-center justify-center z-50">
          <div className="bg-white rounded-t-3xl sm:rounded-2xl w-full sm:w-96 p-6 shadow-xl animate-in slide-in-from-bottom-5 sm:zoom-in-95">
            {/* Header */}
            <div className="text-center mb-6">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Select Time
              </p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                {hour}:{minute} <span className="text-xl">{ampm}</span>
              </p>
            </div>

            {/* Spinner Section */}
            <div className="flex items-center justify-center gap-2 mb-6">
              {/* Hour Spinner */}
              <Spinner
                values={Array.from({ length: 12 }, (_, i) =>
                  String(i + 1).padStart(2, "0")
                )}
                selected={hour}
                onChange={setHour}
                label="Hour"
              />

              {/* Separator */}
              <div className="text-2xl font-bold text-slate-400">:</div>

              {/* Minute Spinner */}
              <Spinner
                values={Array.from({ length: 60 }, (_, i) =>
                  String(i).padStart(2, "0")
                )}
                selected={minute}
                onChange={setMinute}
                label="Minute"
              />

              {/* AM/PM Spinner */}
              <Spinner
                values={["AM", "PM"]}
                selected={ampm}
                onChange={setAmpm}
                label="Period"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => setIsOpen(false)}
                className="flex-1 px-4 py-2.5 border border-slate-200 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDone}
                className="flex-1 px-4 py-2.5 bg-sky-600 text-white font-semibold rounded-lg hover:bg-sky-700 transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface SpinnerProps {
  values: string[];
  selected: string;
  onChange: (value: string) => void;
  label: string;
}

function Spinner({ values, selected, onChange, label }: SpinnerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const itemHeight = 40; // Height of each item in pixels
  const selectedIndex = values.indexOf(selected);

  // Auto-scroll to selected value
  useEffect(() => {
    if (scrollRef.current) {
      const scrollTop = selectedIndex * itemHeight - (3 * itemHeight); // Center it (show 7 items, selected in middle)
      scrollRef.current.scrollTop = Math.max(0, scrollTop);
    }
  }, [selectedIndex]);

  function handleScroll() {
    if (scrollRef.current) {
      const scrollTop = scrollRef.current.scrollTop;
      const index = Math.round(scrollTop / itemHeight);
      const clampedIndex = Math.max(0, Math.min(index, values.length - 1));
      onChange(values[clampedIndex]);
    }
  }

  return (
    <div className="flex flex-col items-center flex-1" ref={containerRef}>
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
        {label}
      </p>

      {/* Scrollable Container */}
      <div className="relative">
        {/* Center highlight line */}
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-10 border-y-2 border-sky-500 pointer-events-none rounded" />

        {/* Scrollable Values */}
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="h-56 w-16 overflow-y-scroll no-scrollbar scroll-smooth"
          style={{
            scrollSnapType: "y mandatory",
            WebkitOverflowScrolling: "touch",
          }}
        >
          {/* Padding top for centering */}
          <div className="h-24" />

          {/* Values */}
          {values.map((value, index) => (
            <div
              key={`${label}-${index}`}
              className={`h-10 flex items-center justify-center font-semibold transition-all duration-200 scroll-snap-align-center ${
                value === selected
                  ? "text-slate-900 text-lg"
                  : "text-slate-400 text-base"
              }`}
            >
              {value}
            </div>
          ))}

          {/* Padding bottom for centering */}
          <div className="h-24" />
        </div>
      </div>
    </div>
  );
}
