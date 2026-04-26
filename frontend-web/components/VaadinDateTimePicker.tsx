"use client";

import { useState, useEffect, useRef } from "react";

interface VaadinDateTimePickerProps {
  value: string; // ISO 8601 datetime string
  onChange: (value: string) => void;
  label: string;
  showTomorrow?: boolean; // Show Tomorrow button instead of Today
  minDateTime?: string; // ISO 8601 datetime string - minimum selectable date/time
}

export default function VaadinDateTimePicker({
  value,
  onChange,
  label,
  showTomorrow = false,
  minDateTime,
}: VaadinDateTimePickerProps) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);

  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  const datePickerRef = useRef<HTMLDivElement>(null);
  const timePickerRef = useRef<HTMLDivElement>(null);

  // Initialize with today's date and current time
  useEffect(() => {
    if (!value) {
      const now = new Date();
      const dateStr = now.toISOString().split("T")[0];
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      const timeStr = `${hours}:${minutes}`;

      setDate(dateStr);
      setTime(timeStr);
      setSelectedDate(now);
    } else {
      try {
        const dt = new Date(value);
        const dateStr = dt.toISOString().split("T")[0];
        const hours = String(dt.getHours()).padStart(2, "0");
        const minutes = String(dt.getMinutes()).padStart(2, "0");
        const timeStr = `${hours}:${minutes}`;

        setDate(dateStr);
        setTime(timeStr);
        setSelectedDate(dt);
        setSelectedYear(dt.getFullYear());
      } catch (e) {
        const now = new Date();
        const dateStr = now.toISOString().split("T")[0];
        setDate(dateStr);
        setSelectedDate(now);
      }
    }
  }, []);

  // Update ISO string
  useEffect(() => {
    if (date && time) {
      try {
        const dateTime = new Date(`${date}T${time}:00`);
        onChange(dateTime.toISOString());
      } catch (e) {
        // Invalid
      }
    }
  }, [date, time, onChange]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (datePickerRef.current && !datePickerRef.current.contains(event.target as Node)) {
        setShowDatePicker(false);
      }
      if (timePickerRef.current && !timePickerRef.current.contains(event.target as Node)) {
        setShowTimePicker(false);
      }
    }

    if (showDatePicker || showTimePicker) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showDatePicker, showTimePicker]);

  function isPastDate(checkDate: Date): boolean {
    // Create a new date object to avoid mutation
    const dateToCheck = new Date(checkDate);
    dateToCheck.setHours(0, 0, 0, 0);

    // If minDateTime is provided, check against it (minimum allowed date)
    if (minDateTime) {
      try {
        const minDate = new Date(minDateTime);
        // Create date at start of day for fair comparison
        const minDateAtStart = new Date(minDate);
        minDateAtStart.setHours(0, 0, 0, 0);
        // Block if date is strictly before the minimum date
        return dateToCheck < minDateAtStart;
      } catch (e) {
        // If minDateTime is invalid, ignore it
      }
    }

    // Otherwise check against today
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return dateToCheck < today;
  }

  function isPastTime(timeStr: string): boolean {
    try {
      // Parse selected date and time
      const [hours, minutes] = timeStr.split(":").map(Number);
      const selectedDateTime = new Date(date);
      selectedDateTime.setHours(hours, minutes || 0, 0, 0);

      // If minDateTime is provided, check against it
      if (minDateTime) {
        try {
          const minDate = new Date(minDateTime);
          // Block if selected date+time is before or equal to minimum
          return selectedDateTime <= minDate;
        } catch (e) {
          // If minDateTime is invalid, ignore it
        }
      }

      // Original logic: check if time has passed today
      const today = new Date();
      const todayAtMidnight = new Date(today);
      todayAtMidnight.setHours(0, 0, 0, 0);

      const selectedDateAtMidnight = new Date(date);
      selectedDateAtMidnight.setHours(0, 0, 0, 0);

      // Only block times for today
      if (selectedDateAtMidnight.getTime() === todayAtMidnight.getTime()) {
        return selectedDateTime < today;
      }

      return false;
    } catch (e) {
      return false;
    }
  }

  function handleDateSelect(day: number) {
    const newDate = new Date(selectedYear, selectedDate.getMonth(), day);

    // Don't allow selecting past dates
    if (isPastDate(newDate)) {
      return;
    }

    setSelectedDate(newDate);
    // Use local date string without timezone conversion
    const dateStr = `${selectedYear}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    setDate(dateStr);
    setShowDatePicker(false);
  }

  function handleToday() {
    const today = new Date();
    setSelectedDate(today);
    setSelectedYear(today.getFullYear());
    // Use local date string without timezone conversion
    const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    setDate(dateStr);
    setShowDatePicker(false);
  }

  function handleTomorrow() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setSelectedDate(tomorrow);
    setSelectedYear(tomorrow.getFullYear());
    // Use local date string without timezone conversion
    const dateStr = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, '0')}-${String(tomorrow.getDate()).padStart(2, '0')}`;
    setDate(dateStr);
    setShowDatePicker(false);
  }

  function getDaysInMonth(year: number, month: number) {
    return new Date(year, month + 1, 0).getDate();
  }

  function getFirstDayOfMonth(year: number, month: number) {
    return new Date(year, month, 1).getDay();
  }

  function renderCalendar(year: number, month: number) {
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    const days = [];

    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} />);
    }

    // Days of month
    for (let day = 1; day <= daysInMonth; day++) {
      const dayDate = new Date(year, month, day);
      const isSelected = date === dayDate.toISOString().split("T")[0];
      const isPast = isPastDate(new Date(year, month, day));

      days.push(
        <button
          key={day}
          onClick={() => handleDateSelect(day)}
          disabled={isPast}
          className={`py-2 text-sm rounded transition-colors ${
            isPast
              ? "text-slate-300 cursor-not-allowed bg-slate-50"
              : isSelected
              ? "bg-sky-500 text-white font-semibold"
              : "text-slate-700 hover:bg-slate-100 cursor-pointer"
          }`}
        >
          {day}
        </button>
      );
    }

    return days;
  }

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const timeOptions = Array.from({ length: 24 }, (_, i) =>
    `${String(i).padStart(2, "0")}:00`
  );

  // Format date for display (Indian format: dd/mm/yyyy)
  const displayDate = date ? new Date(date).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric"
  }) : "";

  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-2">
        {label}
      </label>
      <div className="space-y-2">
        {/* Date Field */}
        <div className="relative" ref={datePickerRef}>
          <button
            onClick={() => {
              setShowDatePicker(!showDatePicker);
              setShowTimePicker(false);
            }}
            className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-900 bg-white hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 text-left flex items-center justify-between"
          >
            {displayDate}
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h18M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>

          {/* Calendar Modal */}
          {showDatePicker && (
            <div className="absolute top-full left-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl z-50 p-4 w-full sm:w-96">
              <div className="flex gap-6">
                {/* Calendar */}
                <div className="flex-1">
                  {/* Month Navigation */}
                  <div className="flex items-center justify-between mb-4">
                    <button
                      onClick={() => setSelectedDate(new Date(selectedYear, selectedDate.getMonth() - 1))}
                      className="text-slate-600 hover:text-slate-900 font-semibold text-lg"
                    >
                      ‹
                    </button>
                    <h3 className="text-center font-semibold text-slate-900 min-w-fit px-2">
                      {monthNames[selectedDate.getMonth()]}
                    </h3>
                    <button
                      onClick={() => setSelectedDate(new Date(selectedYear, selectedDate.getMonth() + 1))}
                      className="text-slate-600 hover:text-slate-900 font-semibold text-lg"
                    >
                      ›
                    </button>
                  </div>

                  {/* Days of week */}
                  <div className="grid grid-cols-7 gap-1 mb-2">
                    {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                      <div key={day} className="text-xs font-semibold text-slate-600 text-center py-1">
                        {day}
                      </div>
                    ))}
                  </div>

                  {/* Calendar days */}
                  <div className="grid grid-cols-7 gap-1">
                    {renderCalendar(selectedYear, selectedDate.getMonth())}
                  </div>
                </div>

                {/* Year Selector */}
                <div className="flex flex-col gap-1">
                  {[selectedYear - 2, selectedYear - 1, selectedYear, selectedYear + 1, selectedYear + 2].map(
                    (year) => (
                      <button
                        key={year}
                        onClick={() => setSelectedYear(year)}
                        className={`px-3 py-1 text-sm rounded transition-colors ${
                          year === selectedYear
                            ? "bg-sky-500 text-white font-semibold"
                            : "text-slate-600 hover:bg-slate-100"
                        }`}
                      >
                        {year}
                      </button>
                    )
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex gap-2 mt-4 pt-4 border-t border-slate-200">
                <button
                  onClick={showTomorrow ? handleTomorrow : handleToday}
                  className="flex-1 py-2 text-sm text-sky-600 hover:bg-sky-50 rounded font-medium"
                >
                  {showTomorrow ? "Tomorrow" : "Today"}
                </button>
                <button
                  onClick={() => setShowDatePicker(false)}
                  className="flex-1 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Time Field */}
        <div className="relative" ref={timePickerRef}>
          <button
            onClick={() => {
              setShowTimePicker(!showTimePicker);
              setShowDatePicker(false);
            }}
            className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-900 bg-white hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 text-left flex items-center justify-between"
          >
            {time}
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 2m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>

          {/* Time Dropdown */}
          {showTimePicker && (
            <div className="absolute top-full left-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
              {timeOptions.map((timeOption) => {
                const isPast = isPastTime(timeOption);
                return (
                  <button
                    key={timeOption}
                    onClick={() => {
                      if (!isPast) {
                        setTime(timeOption);
                        setShowTimePicker(false);
                      }
                    }}
                    disabled={isPast}
                    className={`w-full px-4 py-2.5 text-sm text-left transition-colors ${
                      isPast
                        ? "text-slate-300 cursor-not-allowed bg-slate-50"
                        : time.substring(0, 5) === timeOption
                        ? "bg-sky-500 text-white font-semibold cursor-pointer"
                        : "text-slate-700 hover:bg-slate-100 cursor-pointer"
                    }`}
                  >
                    {timeOption}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
