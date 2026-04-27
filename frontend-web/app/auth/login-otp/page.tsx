"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { saveTokens, saveUser } from "@/lib/auth";

export default function LoginOTPPage() {
  const router = useRouter();
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handlePhoneChange = (value: string) => {
    const digitsOnly = value.replace(/\D/g, "").slice(0, 10);
    setPhone(digitsOnly);
  };

  const isPhoneValid = phone.length === 10;

  async function handleSendOTP() {
    if (!isPhoneValid) {
      setError("Phone number must be 10 digits");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const response = await api.auth.sendOtp(phone);
      setStep("otp");
      if (response.otp) {
        // Dev mode: show OTP for testing
        setError(`Dev Mode - OTP: ${response.otp}`);
      }
    } catch (e: unknown) {
      let errorMsg = "Failed to send OTP";
      if (e instanceof Error) {
        errorMsg = e.message;
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOTP() {
    if (otp.length !== 6) {
      setError("OTP must be 6 digits");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const tokens = await api.auth.verifyOtp(phone, otp);
      saveTokens(tokens);
      const user = await api.auth.me();
      saveUser(user);
      router.push(user.role === "owner" ? "/dashboard/owner" : "/dashboard/bookings");
    } catch (e: unknown) {
      let errorMsg = "Invalid or expired OTP";
      if (e instanceof Error) {
        errorMsg = e.message;
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 w-full max-w-sm">
        <Link href="/" className="text-2xl font-bold text-sky-600 block mb-6">
          Voyza
        </Link>

        <h1 className="text-xl font-bold text-slate-900 mb-1">Sign in with OTP</h1>
        <p className="text-slate-500 text-sm mb-6">Quick and secure login</p>

        {step === "phone" ? (
          <>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">
                  Phone (10 digits)
                </label>
                <div className="flex gap-1 items-center">
                  <span className="text-slate-500 px-3 py-2.5 text-sm font-medium">+91</span>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => handlePhoneChange(e.target.value)}
                    placeholder="9876543210"
                    maxLength={10}
                    className="flex-1 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
              </div>
            </div>

            {error && <p className="text-red-600 text-sm mt-3">{error}</p>}

            <button
              onClick={handleSendOTP}
              disabled={loading || !isPhoneValid}
              className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 rounded-xl mt-5 transition-colors disabled:opacity-40"
            >
              {loading ? "Sending OTP…" : "Send OTP"}
            </button>
          </>
        ) : (
          <>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">
                  OTP Code (6 digits)
                </label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="000000"
                  maxLength={6}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-center text-2xl tracking-widest focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
                <p className="text-xs text-slate-500 mt-2">
                  OTP sent to +91{phone} via SMS
                </p>
              </div>
            </div>

            {error && <p className="text-red-600 text-sm mt-3">{error}</p>}

            <button
              onClick={handleVerifyOTP}
              disabled={loading || otp.length !== 6}
              className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 rounded-xl mt-5 transition-colors disabled:opacity-40"
            >
              {loading ? "Verifying…" : "Sign in"}
            </button>

            <button
              onClick={() => {
                setStep("phone");
                setOtp("");
                setError("");
              }}
              disabled={loading}
              className="w-full mt-3 text-sky-600 font-semibold py-2 hover:underline"
            >
              Change number
            </button>
          </>
        )}

        <p className="text-sm text-slate-500 text-center mt-5">
          Don't have an account?{" "}
          <Link href="/auth/register" className="text-sky-600 font-medium hover:underline">
            Sign up
          </Link>
        </p>

        <p className="text-sm text-slate-500 text-center mt-3">
          Want to use password?{" "}
          <Link href="/auth/login" className="text-sky-600 font-medium hover:underline">
            Sign in with password
          </Link>
        </p>
      </div>
    </div>
  );
}
