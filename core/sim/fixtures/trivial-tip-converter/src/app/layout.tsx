import type { Metadata } from "next";
import "./globals.css";

// NOTE: no `next/font/google` import here on purpose — a remote Google Fonts
// fetch at build time would make `next build` require network access. System
// font stack only (see globals.css), so the build stays offline-green.

export const metadata: Metadata = {
  title: "Trivial Tip Converter",
  description: "A single-page tip calculator and unit converter.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
