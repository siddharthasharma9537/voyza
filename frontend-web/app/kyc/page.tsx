"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";

interface KYCDocument {
  id: string;
  type: string;
  status: "pending" | "verified" | "rejected";
  file_name: string;
  file_url: string;
  document_number?: string;
  expiry_date?: string;
  rejection_reason?: string;
  verified_at?: string;
  uploaded_at: string;
}

interface User {
  id: string;
  role: "customer" | "owner";
  full_name: string;
}

export default function KYCPage() {
  const [user, setUser] = useState<User | null>(null);
  const [documents, setDocuments] = useState<KYCDocument[]>([]);
  const [isVerified, setIsVerified] = useState(false);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [currentDocumentType, setCurrentDocumentType] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const REQUIRED_DOCUMENTS = {
    customer: [
      { type: "driving_license", label: "Driving License", icon: "🪪" },
      { type: "aadhar", label: "Aadhar ID", icon: "📋" },
      { type: "selfie", label: "Selfie (Face Verification)", icon: "🤳" },
    ],
    owner: [
      { type: "driving_license", label: "Driving License", icon: "🪪" },
      { type: "vehicle_rc", label: "Vehicle RC", icon: "📋" },
      { type: "vehicle_insurance", label: "Insurance Policy", icon: "📄" },
    ],
  };

  useEffect(() => {
    fetchKYCStatus();
  }, []);

  async function fetchKYCStatus() {
    try {
      const userData = await api.auth.me();
      setUser(userData as any);

      const [docsData, verifyData] = await Promise.all([
        api.kyc?.documents?.() || Promise.resolve([]),
        api.kyc?.verifyStatus?.() || Promise.resolve({ verified: false }),
      ]);

      setDocuments(docsData || []);
      setIsVerified(verifyData?.verified || false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load KYC status");
    } finally {
      setLoading(false);
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !currentDocumentType) return;

    setUploading(true);
    setError("");

    try {
      // Prepare form data
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", currentDocumentType);

      // For driving license, ask for expiry date
      if (currentDocumentType === "driving_license") {
        const expiryStr = prompt("Enter driving license expiry date (YYYY-MM-DD):");
        if (expiryStr) {
          formData.append("expiry_date", expiryStr);
        }
      }

      // For vehicle insurance, ask for expiry date
      if (currentDocumentType === "vehicle_insurance") {
        const expiryStr = prompt("Enter insurance policy expiry date (YYYY-MM-DD):");
        if (expiryStr) {
          formData.append("expiry_date", expiryStr);
        }
      }

      // Upload via API
      await api.kyc?.uploadDocument?.(formData);

      alert(`Document uploaded successfully: ${file.name}`);
      setCurrentDocumentType("");
      await fetchKYCStatus();
    } catch (e) {
      const message = e instanceof Error ? e.message : "Upload failed";
      setError(message);
      alert(`Upload failed: ${message}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-8 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full"></div>
          <p className="mt-4 text-slate-600">Loading KYC status...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-50 py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-900 font-medium">Please sign in</p>
          </div>
        </div>
      </div>
    );
  }

  const requiredDocs = REQUIRED_DOCUMENTS[user.role];
  const uploadedTypes = new Set(documents.map((d) => d.type));
  const verifiedCount = documents.filter((d) => d.status === "verified").length;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">🔐 KYC Verification</h1>
          <p className="text-slate-600">Verify your identity to unlock full platform access</p>
        </div>

        {/* Verification Status */}
        {isVerified ? (
          <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6 mb-8">
            <div className="flex items-center gap-4">
              <div className="text-5xl">✅</div>
              <div>
                <h2 className="text-xl font-bold text-green-900">Verified!</h2>
                <p className="text-green-800">Your identity has been verified. You're all set to use all platform features.</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mb-8">
            <div className="flex items-center gap-4">
              <div className="text-5xl">⏳</div>
              <div>
                <h2 className="text-xl font-bold text-blue-900">Verification in Progress</h2>
                <p className="text-blue-800">Complete {requiredDocs.length - uploadedTypes.size} more document(s) to verify your identity</p>
              </div>
            </div>
          </div>
        )}

        {/* Progress */}
        <div className="bg-white rounded-lg border border-slate-200 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-900">Documents Progress</h2>
            <span className="text-2xl font-bold text-sky-600">
              {uploadedTypes.size}/{requiredDocs.length}
            </span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div
              className="bg-sky-600 h-3 rounded-full transition-all"
              style={{ width: `${(uploadedTypes.size / requiredDocs.length) * 100}%` }}
            ></div>
          </div>
          <p className="text-sm text-slate-600 mt-2">
            {uploadedTypes.size === requiredDocs.length ? "All documents uploaded! Awaiting verification." : "Upload all required documents to proceed."}
          </p>
        </div>

        {/* Required Documents */}
        <div className="space-y-4 mb-8">
          {requiredDocs.map((docType) => {
            const uploaded = documents.find((d) => d.type === docType.type);
            const isVerified = uploaded?.status === "verified";
            const isRejected = uploaded?.status === "rejected";

            return (
              <div
                key={docType.type}
                className={`border-2 rounded-lg p-6 transition-all ${
                  isVerified
                    ? "bg-green-50 border-green-300"
                    : isRejected
                      ? "bg-red-50 border-red-300"
                      : uploaded
                        ? "bg-blue-50 border-blue-300"
                        : "bg-white border-slate-200 hover:border-slate-300"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4 flex-1">
                    <span className="text-3xl">{docType.icon}</span>
                    <div>
                      <h3 className="font-bold text-slate-900">{docType.label}</h3>
                      {uploaded && (
                        <div className="mt-2 text-sm space-y-1">
                          <p className="text-slate-600">
                            <strong>File:</strong> {uploaded.file_name}
                          </p>
                          {uploaded.document_number && (
                            <p className="text-slate-600">
                              <strong>Number:</strong> {uploaded.document_number}
                            </p>
                          )}
                          {uploaded.expiry_date && (
                            <p className="text-slate-600">
                              <strong>Expires:</strong> {new Date(uploaded.expiry_date).toLocaleDateString()}
                            </p>
                          )}
                          <p
                            className={`font-medium ${
                              isVerified ? "text-green-700" : isRejected ? "text-red-700" : "text-blue-700"
                            }`}
                          >
                            {isVerified ? "✓ Verified" : isRejected ? "✕ Rejected" : "⏳ Pending Review"}
                          </p>
                          {isRejected && uploaded.rejection_reason && (
                            <p className="text-red-700">
                              <strong>Reason:</strong> {uploaded.rejection_reason}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="text-right">
                    {isVerified && <div className="text-4xl">✅</div>}
                    {isRejected && <div className="text-4xl">❌</div>}
                    {!uploaded && (
                      <button
                        onClick={() => {
                          setCurrentDocumentType(docType.type);
                          fileInputRef.current?.click();
                        }}
                        disabled={uploading}
                        className="bg-sky-600 hover:bg-sky-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                      >
                        {uploading ? "Uploading..." : "Upload"}
                      </button>
                    )}
                    {uploaded && !isVerified && (
                      <button
                        onClick={() => {
                          setCurrentDocumentType(docType.type);
                          fileInputRef.current?.click();
                        }}
                        className="bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg font-medium transition-colors text-sm"
                      >
                        Resubmit
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <p className="text-sm text-blue-900 mb-3">
            <strong>ℹ️ Why we need these documents:</strong>
          </p>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>• <strong>Driving License:</strong> Confirms you're authorized to drive</li>
            <li>• <strong>Aadhar/ID:</strong> Verifies your identity</li>
            <li>• <strong>Selfie:</strong> Live face verification for security</li>
            <li>• <strong>Vehicle RC:</strong> Confirms vehicle ownership (owners only)</li>
            <li>• <strong>Insurance:</strong> Ensures vehicle is insured (owners only)</li>
          </ul>
          <p className="text-sm text-blue-800 mt-4">
            All documents are encrypted and stored securely. We never share your personal information with third parties.
          </p>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>
    </div>
  );
}
