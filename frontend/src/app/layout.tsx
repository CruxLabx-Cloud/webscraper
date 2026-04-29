import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ScrapeFlow",
  description: "From URL to structured data in seconds.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background antialiased">{children}</body>
    </html>
  );
}
