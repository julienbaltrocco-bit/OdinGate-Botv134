import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Self-hosted font (no Google Fonts request; DSGVO-friendly).
const inter = localFont({
  src: [
    { path: "../../assets/fonts/Inter-Regular.otf", weight: "400" },
    { path: "../../assets/fonts/Inter-SemiBold.otf", weight: "600" },
    { path: "../../assets/fonts/Inter-Bold.otf", weight: "700" },
  ],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Content Engine",
  description: "KI-native Content- und Growth-Infrastruktur",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full">{children}</body>
    </html>
  );
}
