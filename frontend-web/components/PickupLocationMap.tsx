"use client";

import { useEffect, useRef } from "react";

interface PickupLocationMapProps {
  latitude?: number | string | null;
  longitude?: number | string | null;
  address?: string | null;
  vehicleName?: string;
}

/**
 * Displays pickup location on a map using Google Maps or fallback.
 * In production, integrate with Google Maps API or Mapbox.
 * For now, shows directions link and location details.
 */
export function PickupLocationMap({
  latitude,
  longitude,
  address,
  vehicleName,
}: PickupLocationMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);

  // Generate Google Maps link
  const getMapsLink = () => {
    if (latitude && longitude) {
      return `https://maps.google.com/?q=${latitude},${longitude}`;
    }
    if (address) {
      return `https://maps.google.com/?q=${encodeURIComponent(address)}`;
    }
    return null;
  };

  const mapsLink = getMapsLink();

  return (
    <div className="w-full">
      <div
        ref={mapContainerRef}
        className="w-full h-64 bg-gradient-to-br from-slate-100 to-slate-200 rounded-lg flex items-center justify-center relative overflow-hidden"
      >
        {/* Placeholder Map */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-4xl mb-2">📍</div>
          <p className="text-slate-600 text-sm text-center px-4 font-medium">
            {address || "Pickup Location"}
          </p>

          {/* Map Controls Mockup */}
          <div className="absolute top-3 right-3 flex gap-2">
            <button className="bg-white rounded-lg p-2 shadow-sm hover:shadow-md transition-shadow">
              <span className="text-lg">🔍</span>
            </button>
            <button className="bg-white rounded-lg p-2 shadow-sm hover:shadow-md transition-shadow">
              <span className="text-lg">🧭</span>
            </button>
          </div>

          {/* Zoom Controls */}
          <div className="absolute right-3 top-14 flex flex-col gap-1">
            <button className="bg-white rounded px-2 py-1 shadow-sm hover:shadow-md text-sm font-bold">
              +
            </button>
            <button className="bg-white rounded px-2 py-1 shadow-sm hover:shadow-md text-sm font-bold">
              −
            </button>
          </div>
        </div>
      </div>

      {/* Location Details */}
      <div className="mt-4 space-y-3">
        {address && (
          <div className="flex gap-3">
            <span className="text-lg">📍</span>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Pickup Address</p>
              <p className="text-sm font-medium text-slate-900">{address}</p>
            </div>
          </div>
        )}

        {latitude && longitude && (
          <div className="flex gap-3 text-xs text-slate-600">
            <span>📌</span>
            <span>
              Coordinates: {Number(latitude).toFixed(4)}°, {Number(longitude).toFixed(4)}°
            </span>
          </div>
        )}

        {/* Directions Button */}
        {mapsLink && (
          <div className="mt-4 flex gap-2">
            <a
              href={mapsLink}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center gap-2 bg-blue-100 hover:bg-blue-200 text-blue-700 font-semibold py-2 rounded-lg transition-colors"
            >
              <span>🗺️</span>
              Get Directions
            </a>
            <button
              onClick={() => {
                if (navigator.share) {
                  navigator.share({
                    title: `${vehicleName} Pickup Location`,
                    text: address || "Pickup location",
                    url: window.location.href,
                  });
                }
              }}
              className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg transition-colors"
            >
              📤
            </button>
          </div>
        )}

        {/* Distance Estimate */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
          <p className="text-blue-900">
            <strong>💡 Tip:</strong> Allow extra time for traffic. We recommend arriving 15 minutes early.
          </p>
        </div>
      </div>
    </div>
  );
}
