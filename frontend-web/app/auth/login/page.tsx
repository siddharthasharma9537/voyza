"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { saveTokens, saveUser } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"password" | "otp">("password");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [devOtp, setDevOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSendOtp() {
    setLoading(true); setError("");
    try {
      const res = await api.auth.sendOtp(phone);
      setOtpSent(true);
      if (res.otp) setDevOtp(res.otp); // dev mode: backend returns OTP
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to send OTP");
    } finally { setLoading(false); }
  }

  async function handleLogin() {
    setLoading(true); setError("");
    try {
      let tokens;
      if (mode === "password") {
        tokens = await api.auth.login(phone, password);
      } else {
        tokens = await api.auth.verifyOtp(phone, otp);
      }
      saveTokens(tokens);
      const user = await api.auth.me();
      saveUser(user);
      router.push(user.role === "owner" ? "/dashboard/owner" : "/dashboard/bookings");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Login failed");
    } finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 w-full max-w-sm">
        <Link href="/" className="text-2xl font-bold text-sky-600 block mb-6">Voyza</Link>

        <h1 className="text-xl font-bold text-slate-900 mb-1">Welcome back</h1>
        <p className="text-slate-500 text-sm mb-6">Sign in to continue</p>

        {/* Mode toggle */}
        <div className="flex bg-slate-100 rounded-lg p-1 mb-5">
          {(["password", "otp"] as const).map((m) => (
            <button key={m} onClick={() => { setMode(m); setError(""); }}
              className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${mode === m ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"}`}>
              {m === "password" ? "Password" : "OTP"}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Phone (10 digits)</label>
            <div className="flex gap-1 items-center">
              <span className="text-slate-500 px-3 py-2.5 text-sm font-medium">+91</span>
              <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                placeholder="9876543210"
                maxLength={10}
                className="flex-1 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
            </div>
          </div>

          {mode === "password" && (
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
            </div>
          )}

          {mode === "otp" && !otpSent && (
            <button onClick={handleSendOtp} disabled={!phone || loading}
              className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-2.5 rounded-lg text-sm disabled:opacity-40">
              {loading ? "Sending…" : "Send OTP"}
            </button>
          )}

          {mode === "otp" && otpSent && (
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">OTP</label>
              <input type="text" value={otp} onChange={(e) => setOtp(e.target.value)}
                placeholder="6-digit code" maxLength={6}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
              {devOtp && (
                <p className="text-xs text-amber-600 mt-1 bg-amber-50 px-2 py-1 rounded">
                  Dev: OTP is <strong>{devOtp}</strong>
                </p>
              )}
            </div>
          )}
        </div>

        {error && <p className="text-red-600 text-sm mt-3">{error}</p>}

        {(mode === "password" || otpSent) && (
          <button onClick={handleLogin}
            disabled={loading || (mode === "password" ? !phone || !password : !otp)}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 rounded-xl mt-5 transition-colors disabled:opacity-40">
            {loading ? "Signing in…" : "Sign in"}
          </button>
        )}

        <p className="text-sm text-slate-500 text-center mt-5">
          No account?{" "}
          <Link href="/auth/register" className="text-sky-600 font-medium hover:underline">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
