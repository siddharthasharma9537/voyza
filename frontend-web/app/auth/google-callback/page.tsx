"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { saveTokens, saveUser } from "@/lib/auth";

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get("code");
        const state = searchParams.get("state");

        if (!code) {
          setError("No authorization code received from Google");
          setLoading(false);
          return;
        }

        // Exchange code for tokens via backend
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/auth/oauth/google/callback?code=${encodeURIComponent(code)}`,
          { method: "GET" }
        );

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || "OAuth authentication failed");
        }

        const tokens = await response.json();
        saveTokens(tokens);

        // Get user profile
        const user = await api.auth.me();
        saveUser(user);

        // Redirect based on user role
        router.push(user.role === "owner" ? "/dashboard/owner" : "/dashboard/bookings");
      } catch (e: unknown) {
        let errorMsg = "Authentication failed";
        if (e instanceof Error) {
          errorMsg = e.message;
        }
        setError(errorMsg);
        setLoading(false);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Completing sign up...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 w-full max-w-sm">
          <p className="text-red-600 text-sm mb-4">{error}</p>
          <button
            onClick={() => router.push("/auth/register")}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            Back to Sign Up
          </button>
        </div>
      </div>
    );
  }

  return null;
}
