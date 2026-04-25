import Link from "next/link";
import { formatRupees, fuelLabel, transmissionLabel } from "@/lib/api";
import type { VehicleListItem } from "@/lib/api";

export default function VehicleCard({ v }: { v: VehicleListItem }) {
  return (
    <Link
      href={`/cars/${v.id}`}
      className="group bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-lg transition-shadow"
    >
      <div className="relative h-48 bg-slate-100">
        {v.primary_image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={v.primary_image}
            alt={`${v.make} ${v.model}`}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-300">
            <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
                d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
                d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10l2 2h10l2-2zM16 16V8a1 1 0 00-1-1h-2l-3 3v6h6z" />
            </svg>
          </div>
        )}
        <span className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm text-xs font-semibold text-slate-700 px-2 py-1 rounded-full">
          {v.city}
        </span>
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-slate-900 text-lg leading-tight">
          {v.make} {v.model} {v.variant ?? ""}
        </h3>
        <p className="text-slate-500 text-sm mt-0.5">{v.year}</p>

        <div className="flex flex-wrap gap-2 mt-3">
          <Tag>{fuelLabel(v.fuel_type)}</Tag>
          <Tag>{transmissionLabel(v.transmission)}</Tag>
          <Tag>{v.seating} seats</Tag>
        </div>

        <div className="flex items-end justify-between mt-4">
          <div>
            <span className="text-xl font-bold text-slate-900">{formatRupees(v.price_per_day)}</span>
            <span className="text-slate-500 text-sm">/day</span>
          </div>
          {v.avg_rating && (
            <div className="flex items-center gap-1 text-sm text-amber-500">
              <span>★</span>
              <span className="font-medium text-slate-700">{v.avg_rating.toFixed(1)}</span>
              <span className="text-slate-400">({v.review_count})</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{children}</span>
  );
}
