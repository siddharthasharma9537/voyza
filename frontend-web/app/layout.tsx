import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Voyza — Rent Cars Near You",
  description: "Find and rent cars from local owners. Affordable, flexible, trusted.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col antialiased">{children}</body>
    </html>
  );
}
