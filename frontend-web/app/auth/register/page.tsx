"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { saveTokens, saveUser } from "@/lib/auth";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const defaultRole = searchParams.get("role") === "owner" ? "owner" : "customer";

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"customer" | "owner">(defaultRole as "customer" | "owner");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [googleLoading, setGoogleLoading] = useState(false);

  // Format phone number: remove all non-digits as user types
  const handlePhoneChange = (value: string) => {
    const digitsOnly = value.replace(/\D/g, "").slice(0, 10);
    setPhone(digitsOnly);
  };

  // Validation: phone must have 10 digits
  const isPhoneValid = phone.length === 10;

  async function handleRegister() {
    if (!isPhoneValid) {
      setError("Phone number must be 10 digits");
      return;
    }

    setLoading(true); setError("");
    try {
      const response = await api.auth.register({ full_name: fullName, email: email || undefined, phone, password, role });
      const tokens = await api.auth.login(phone, password);
      saveTokens(tokens);
      const user = await api.auth.me();
      saveUser(user);
      router.push(role === "owner" ? "/dashboard/owner" : "/dashboard/bookings");
    } catch (e: unknown) {
      let errorMsg = "Registration failed";
      if (e instanceof Error) {
        errorMsg = e.message;
      } else if (typeof e === "string") {
        errorMsg = e;
      } else if (e && typeof e === "object" && "message" in e) {
        errorMsg = String((e as any).message);
      }
      setError(errorMsg);
      console.error("Registration error:", e);
    } finally { setLoading(false); }
  }

  async function handleGoogleLogin() {
    setGoogleLoading(true);
    try {
      const redirectUri = `${window.location.origin}/auth/google-callback`;
      const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
      if (!clientId) {
        setError("Google OAuth not configured");
        return;
      }
      const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=openid%20email%20profile`;
      window.location.href = googleAuthUrl;
    } catch (e: unknown) {
      let errorMsg = "Google login failed";
      if (e instanceof Error) {
        errorMsg = e.message;
      }
      setError(errorMsg);
      setGoogleLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 w-full max-w-sm">
        <Link href="/" className="text-2xl font-bold text-sky-600 block mb-6">Voyza</Link>

        <h1 className="text-xl font-bold text-slate-900 mb-1">Create account</h1>
        <p className="text-slate-500 text-sm mb-6">Join Voyza today</p>

        {/* Role toggle */}
        <div className="flex bg-slate-100 rounded-lg p-1 mb-5">
          {(["customer", "owner"] as const).map((r) => (
            <button key={r} onClick={() => setRole(r)}
              className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors capitalize ${role === r ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"}`}>
              {r === "customer" ? "Rent a car" : "List my car"}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Full name</label>
            <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)}
              placeholder="Ravi Kumar"
              className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Email (optional)</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="ravi@example.com"
              className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
          </div>

          {/* Phone */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Phone (10 digits)</label>
            <div className="flex gap-1 items-center">
              <span className="text-slate-500 px-3 py-2.5 text-sm font-medium">+91</span>
              <input type="tel" value={phone} onChange={(e) => handlePhoneChange(e.target.value)}
                placeholder="9876543210"
                maxLength={10}
                className="flex-1 border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 8 characters"
              className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
          </div>
        </div>

        {error && <p className="text-red-600 text-sm mt-3">{error}</p>}

        <button onClick={handleRegister}
          disabled={loading || !fullName || !isPhoneValid || !password}
          className="w-full bg-sky-600 hover:bg-sky-700 text-white font-semibold py-3 rounded-xl mt-5 transition-colors disabled:opacity-40">
          {loading ? "Creating account…" : "Create account"}
        </button>

        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200"></div>
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="px-2 bg-white text-slate-500">or</span>
          </div>
        </div>

        <button onClick={handleGoogleLogin}
          disabled={googleLoading || loading}
          type="button"
          className="w-full border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-40">
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          {googleLoading ? "Signing up…" : "Sign up with Google"}
        </button>

        <p className="text-sm text-slate-500 text-center mt-5">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-sky-600 font-medium hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return <Suspense><RegisterForm /></Suspense>;
}
