"use client";

import { useState, useRef } from "react";

export interface DamageReport {
  damage_type: string;
  description: string;
  damage_photos: string[];
  estimated_cost?: number;
}

interface DamageReportFormProps {
  bookingId: string;
  onSubmit?: (report: DamageReport) => void;
  disabled?: boolean;
}

const DAMAGE_TYPES = [
  { id: "scratch", label: "🖌️ Scratch", description: "Minor surface scratch" },
  { id: "dent", label: "🔨 Dent", description: "Body dent or denting" },
  { id: "broken_glass", label: "🪟 Broken Glass", description: "Windshield, window, or mirror" },
  { id: "tire_damage", label: "🛞 Tire Damage", description: "Tire puncture or damage" },
  { id: "interior_damage", label: "🪑 Interior Damage", description: "Seat, dashboard, upholstery" },
  { id: "engine_damage", label: "⚙️ Engine Damage", description: "Mechanical issue" },
  { id: "major_accident", label: "💥 Major Accident", description: "Significant structural damage" },
  { id: "other", label: "📝 Other", description: "Other damage type" },
];

export function DamageReportForm({ bookingId, onSubmit, disabled = false }: DamageReportFormProps) {
  const [selectedType, setSelectedType] = useState<string>("");
  const [description, setDescription] = useState("");
  const [photos, setPhotos] = useState<string[]>([]);
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [estimatedCost, setEstimatedCost] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handlePhotoSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files) return;

    const newFiles = Array.from(files);

    // Validate file count (max 5 photos)
    if (photoFiles.length + newFiles.length > 5) {
      alert("Maximum 5 photos allowed");
      return;
    }

    // Validate file types and size
    const validFiles: File[] = [];
    for (const file of newFiles) {
      if (!file.type.startsWith("image/")) {
        alert(`Invalid file type: ${file.name}. Only images allowed.`);
        continue;
      }
      if (file.size > 10 * 1024 * 1024) { // 10MB max
        alert(`File too large: ${file.name}. Maximum size is 10MB.`);
        continue;
      }
      validFiles.push(file);
    }

    setPhotoFiles([...photoFiles, ...validFiles]);

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function removePhoto(index: number) {
    setPhotoFiles(photoFiles.filter((_, i) => i !== index));
  }

  async function handleSubmit() {
    if (!selectedType || !description) {
      alert("Please select damage type and provide description");
      return;
    }

    setSubmitting(true);
    try {
      // TODO: Upload photos to S3 and get URLs
      // For now, photos will be empty - need to integrate S3 upload service
      // This would happen after user submits damage report and before calling onSubmit

      const report: DamageReport = {
        damage_type: selectedType,
        description,
        damage_photos: photos, // Currently empty - photos need S3 upload
        estimated_cost: estimatedCost ? parseInt(estimatedCost) * 100 : undefined, // Convert to paise
      };

      // Note: In a real implementation, we'd upload photoFiles to S3 first,
      // get the URLs, and then include them in the report

      onSubmit?.(report);
    } catch (error) {
      console.error("Error submitting damage report:", error);
      alert(`Failed to submit: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
      <h2 className="text-lg font-bold text-slate-900 mb-4">🔍 Report Damage</h2>

      {/* Damage Type Selection */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-slate-900 mb-3">Damage Type</label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {DAMAGE_TYPES.map((type) => (
            <button
              key={type.id}
              onClick={() => setSelectedType(type.id)}
              disabled={disabled}
              className={`p-3 rounded-lg border-2 transition-all text-left ${
                selectedType === type.id
                  ? "bg-red-50 border-red-300"
                  : "bg-white border-slate-200 hover:border-slate-300"
              } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            >
              <p className="font-semibold text-slate-900">{type.label}</p>
              <p className="text-xs text-slate-600">{type.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Description */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-slate-900 mb-2">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={disabled || submitting}
          placeholder="Describe the damage in detail (location, size, circumstances...)"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
          rows={4}
        />
      </div>

      {/* Estimated Cost */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-slate-900 mb-2">Estimated Repair Cost (₹)</label>
        <input
          type="number"
          value={estimatedCost}
          onChange={(e) => setEstimatedCost(e.target.value)}
          disabled={disabled || submitting}
          placeholder="Estimated cost in rupees"
          className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
        />
      </div>

      {/* Photo Upload */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-slate-900 mb-3">📸 Damage Photos (Optional but Recommended)</label>
        <div className="border-2 border-dashed border-slate-300 rounded-lg p-4 text-center hover:border-slate-400 transition-colors">
          <p className="text-sm text-slate-600 mb-3">Upload up to 5 photos of the damage</p>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || submitting || photoFiles.length >= 5}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {photoFiles.length >= 5 ? "Maximum photos reached" : "Choose Files"}
          </button>
          <p className="text-xs text-slate-500 mt-2">{photoFiles.length}/5 photos selected</p>
        </div>

        {/* Photo Thumbnails */}
        {photoFiles.length > 0 && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4">
            {photoFiles.map((file, index) => (
              <div key={index} className="relative">
                <img
                  src={URL.createObjectURL(file)}
                  alt={`Damage photo ${index + 1}`}
                  className="w-full h-32 object-cover rounded-lg border border-slate-200"
                />
                <button
                  type="button"
                  onClick={() => removePhoto(index)}
                  disabled={disabled || submitting}
                  className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold transition-colors disabled:opacity-50"
                  title="Remove photo"
                >
                  ×
                </button>
                <p className="text-xs text-slate-600 mt-1 truncate">{file.name}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*"
        onChange={handlePhotoSelect}
        disabled={disabled || submitting}
        className="hidden"
      />

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={disabled || submitting || !selectedType}
        className="w-full bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? "Submitting..." : "Submit Damage Report"}
      </button>

      {/* Info Banner */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
        <p className="text-blue-900 mb-2">
          <strong>📋 What happens next?</strong>
        </p>
        <ul className="text-blue-800 space-y-1 ml-4">
          <li>• Your report will be reviewed by our team</li>
          <li>• Owner will be notified of the damage claim</li>
          <li>• If accepted, compensation will be processed</li>
          <li>• You'll get updates via SMS and in-app</li>
        </ul>
      </div>
    </div>
  );
}
