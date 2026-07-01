import type { Metadata } from "next";
import { DM_Sans, Syne, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/auth-context";

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-dm-sans",
});

const syne = Syne({
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  variable: "--font-syne",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-space",
});

export const metadata: Metadata = {
  title: "FWC AI-HRMS — Intelligent Human Resource Management",
  description: "AI-powered Human Resource Management System by FWC IT Services.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${dmSans.variable} ${syne.variable} ${spaceGrotesk.variable} antialiased`}
    >
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
