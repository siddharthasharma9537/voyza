"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { saveTokens, saveUser } from "@/lib/auth";

// Country codes and their phone number lengths
const COUNTRIES = [
  { code: "91", country: "🇮🇳 India", length: 10 },
  { code: "1", country: "🇺🇸 United States", length: 10 },
  { code: "44", country: "🇬🇧 United Kingdom", length: 10 },
  { code: "61", country: "🇦🇺 Australia", length: 9 },
  { code: "1", country: "🇨🇦 Canada", length: 10 },
  { code: "86", country: "🇨🇳 China", length: 11 },
];

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const defaultRole = searchParams.get("role") === "owner" ? "owner" : "customer";

  const [fullName, setFullName] = useState("");
  const [countryCode, setCountryCode] = useState("91"); // Default to India
  const [phoneLocal, setPhoneLocal] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"customer" | "owner">(defaultRole as "customer" | "owner");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Format phone number: remove all non-digits as user types
  const handlePhoneChange = (value: string) => {
    const digitsOnly = value.replace(/\D/g, "");
    setPhoneLocal(digitsOnly);
  };

  // Get the current country's phone length
  const currentCountry = COUNTRIES.find(c => c.code === countryCode);
  const expectedLength = currentCountry?.length || 10;

  // Format as E.164 (+{countryCode}{localPhone})
  const formattedPhone = phoneLocal ? `+${countryCode}${phoneLocal}` : "";

  // Validation: phone must have correct length
  const isPhoneValid = phoneLocal.length === expectedLength;

  async function handleRegister() {
    if (!isPhoneValid) {
      setError(`Phone number must be ${expectedLength} digits`);
      return;
    }

    setLoading(true); setError("");
    try {
      await api.auth.register({ full_name: fullName, phone: formattedPhone, password, role });
      const tokens = await api.auth.login(formattedPhone, password);
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

          {/* Country Code + Phone */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Phone number</label>
            <div className="flex gap-2">
              {/* Country selector */}
              <select value={countryCode} onChange={(e) => setCountryCode(e.target.value)}
                className="flex-shrink-0 border border-slate-200 rounded-lg px-2 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white">
                {COUNTRIES.map(c => (
                  <option key={c.code + c.country} value={c.code}>{c.country}</option>
                ))}
              </select>

              {/* Phone input */}
              <div className="flex-1 relative">
                <input type="tel" value={phoneLocal} onChange={(e) => handlePhoneChange(e.target.value)}
                  placeholder={`${expectedLength} digits`}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500" />
                {phoneLocal && (
                  <div className="absolute right-3 top-2.5 text-xs text-slate-400">
                    {phoneLocal.length}/{expectedLength}
                  </div>
                )}
              </div>
            </div>

            {/* Display formatted number */}
            {formattedPhone && (
              <p className="text-xs text-slate-500 mt-1">
                Formatted: <span className="font-mono font-semibold text-slate-700">{formattedPhone}</span>
              </p>
            )}
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
