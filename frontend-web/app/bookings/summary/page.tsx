import { Suspense } from "react";
import BookingSummaryContent from "./content";

export default function BookingSummaryPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full"></div>
          <p className="mt-4 text-slate-600">Loading your booking...</p>
        </div>
      </div>
    }>
      <BookingSummaryContent />
    </Suspense>
  );
}
