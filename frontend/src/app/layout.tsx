import type { Metadata, Viewport } from "next";
import { Space_Grotesk, IBM_Plex_Sans } from "next/font/google";
import { ErrorBoundary } from "@/components/error-boundary";
import { SiteNav } from "@/components/site-nav";
import "./globals.css";

const headingFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: ["600", "700"],
});

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Company Intelligence Tracker",
  description:
    "C-suite leadership profiles, multi-platform job postings, and email digests for any company.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${headingFont.variable} ${bodyFont.variable}`}>
      <head>
        <meta charSet="utf-8" />
        <meta property="og:title" content="Company Intelligence Tracker" />
        <meta
          property="og:description"
          content="Aggregate leadership and live hiring signals for any company."
        />
      </head>
      <body className="min-h-screen antialiased">
        <ErrorBoundary>
          <SiteNav />
          <main>{children}</main>
        </ErrorBoundary>
      </body>
    </html>
  );
}