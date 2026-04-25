"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { clearTokens, clearUser, getStoredUser } from "@/lib/auth";
import type { User } from "@/lib/api";

export default function Navbar() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  async function logout() {
    const rt = localStorage.getItem("refresh_token") ?? "";
    try { await api.auth.logout(rt); } catch {}
    clearTokens();
    clearUser();
    setUser(null);
    router.push("/");
  }

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
        <Link href="/" className="text-2xl font-bold text-sky-600 tracking-tight">
          Voyza
        </Link>

        <div className="flex items-center gap-4">
          <Link href="/cars" className="text-sm text-slate-600 hover:text-sky-600 font-medium">
            Browse Cars
          </Link>

          {!user ? (
            <>
              <Link
                href="/auth/login"
                className="text-sm text-slate-600 hover:text-sky-600 font-medium"
              >
                Log in
              </Link>
              <Link
                href="/auth/register"
                className="text-sm bg-sky-600 text-white px-4 py-2 rounded-lg hover:bg-sky-700 font-medium"
              >
                Sign up
              </Link>
            </>
          ) : (
            <div className="relative">
              <button
                onClick={() => setOpen((o) => !o)}
                className="flex items-center gap-2 text-sm font-medium text-slate-700 hover:text-sky-600"
              >
                <span className="w-8 h-8 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center font-bold uppercase">
                  {user.full_name[0]}
                </span>
                <span className="hidden sm:inline">{user.full_name.split(" ")[0]}</span>
              </button>

              {open && (
                <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-xl shadow-lg py-1 z-50">
                  {user.role === "owner" && (
                    <Link
                      href="/dashboard/owner"
                      onClick={() => setOpen(false)}
                      className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      Owner Dashboard
                    </Link>
                  )}
                  <Link
                    href="/dashboard/bookings"
                    onClick={() => setOpen(false)}
                    className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                  >
                    My Bookings
                  </Link>
                  <hr className="my-1 border-slate-100" />
                  <button
                    onClick={logout}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    Log out
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
