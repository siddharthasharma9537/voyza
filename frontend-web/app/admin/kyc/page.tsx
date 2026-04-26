"use client";

import { useState, useEffect } from "react";
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
  user_id?: string;
  user_name?: string;
}

export default function AdminKYCPage() {
  const [documents, setDocuments] = useState<KYCDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "pending" | "verified" | "rejected">("pending");
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<KYCDocument | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");

  useEffect(() => {
    fetchDocuments();
  }, []);

  async function fetchDocuments() {
    setLoading(true);
    try {
      // Fetch all documents (users field will only show up if user is admin)
      const allDocs = await api.kyc?.documents?.() as any[];
      setDocuments(allDocs || []);
    } catch (e) {
      console.error("Failed to fetch documents:", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(docId: string) {
    setProcessingId(docId);
    try {
      await api.kyc?.verifyDocument?.(docId, "Document verified by admin");
      alert("Document verified successfully!");
      await fetchDocuments();
    } catch (e) {
      alert(`Failed to verify: ${e instanceof Error ? e.message : "Unknown error"}`);
    } finally {
      setProcessingId(null);
    }
  }

  async function handleReject() {
    if (!selectedDoc || !rejectionReason.trim()) {
      alert("Please provide a rejection reason");
      return;
    }

    setProcessingId(selectedDoc.id);
    try {
      await api.kyc?.rejectDocument?.(selectedDoc.id, rejectionReason);
      alert("Document rejected successfully!");
      setSelectedDoc(null);
      setRejectionReason("");
      await fetchDocuments();
    } catch (e) {
      alert(`Failed to reject: ${e instanceof Error ? e.message : "Unknown error"}`);
    } finally {
      setProcessingId(null);
    }
  }

  const filteredDocs = documents.filter((doc) => filter === "all" || doc.status === filter);
  const stats = {
    pending: documents.filter((d) => d.status === "pending").length,
    verified: documents.filter((d) => d.status === "verified").length,
    rejected: documents.filter((d) => d.status === "rejected").length,
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-8 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full"></div>
          <p className="mt-4 text-slate-600">Loading documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">🔐 KYC Document Management</h1>
          <p className="text-slate-600">Review and verify customer and owner documents</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="text-3xl font-bold text-orange-600 mb-2">{stats.pending}</div>
            <p className="text-slate-600">Pending Review</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="text-3xl font-bold text-green-600 mb-2">{stats.verified}</div>
            <p className="text-slate-600">Verified</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <div className="text-3xl font-bold text-red-600 mb-2">{stats.rejected}</div>
            <p className="text-slate-600">Rejected</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6 border-b border-slate-200">
          {(["all", "pending", "verified", "rejected"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 font-medium capitalize transition-colors ${
                filter === f
                  ? "text-sky-600 border-b-2 border-sky-600"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {f === "all" ? "All Documents" : f}
            </button>
          ))}
        </div>

        {/* Documents Table */}
        {filteredDocs.length === 0 ? (
          <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
            <p className="text-slate-500 text-lg">No documents found</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">User</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">Document Type</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">File</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">Uploaded</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">Status</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-slate-900">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-6 py-4 text-sm text-slate-900">{doc.user_name || "User"}</td>
                    <td className="px-6 py-4 text-sm text-slate-600 capitalize">{doc.type.replace("_", " ")}</td>
                    <td className="px-6 py-4 text-sm text-sky-600 hover:underline">
                      <a href={doc.file_url} target="_blank" rel="noopener noreferrer">
                        {doc.file_name}
                      </a>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {doc.status === "pending" && (
                        <span className="inline-block bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-xs font-semibold">
                          ⏳ Pending
                        </span>
                      )}
                      {doc.status === "verified" && (
                        <span className="inline-block bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-semibold">
                          ✓ Verified
                        </span>
                      )}
                      {doc.status === "rejected" && (
                        <span className="inline-block bg-red-100 text-red-800 px-3 py-1 rounded-full text-xs font-semibold">
                          ✕ Rejected
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right text-sm gap-2 flex justify-end">
                      {doc.status === "pending" && (
                        <>
                          <button
                            onClick={() => handleVerify(doc.id)}
                            disabled={processingId === doc.id}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors disabled:opacity-50"
                          >
                            {processingId === doc.id ? "..." : "Verify"}
                          </button>
                          <button
                            onClick={() => setSelectedDoc(doc)}
                            disabled={processingId === doc.id}
                            className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors disabled:opacity-50"
                          >
                            Reject
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Rejection Modal */}
        {selectedDoc && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-4">Reject Document</h2>
              <p className="text-slate-600 mb-4">
                Document: <strong>{selectedDoc.file_name}</strong>
              </p>

              <div className="mb-4">
                <label className="block text-sm font-semibold text-slate-900 mb-2">Rejection Reason</label>
                <textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Explain why this document was rejected..."
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
                  rows={4}
                />
              </div>

              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setSelectedDoc(null);
                    setRejectionReason("");
                  }}
                  className="px-4 py-2 text-slate-700 border border-slate-300 rounded-lg font-medium hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReject}
                  disabled={processingId === selectedDoc.id}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  {processingId === selectedDoc.id ? "Processing..." : "Reject"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
