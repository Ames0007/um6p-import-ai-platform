import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Providers } from "./providers";
import { AppShell } from "@/components/layout/app-shell";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Assistant IA Import UM6P",
    template: "%s · Assistant IA Import UM6P",
  },
  description:
    "Copilote IA pour les opérations d'importation, les codes SH, les taxes douanières et les exigences réglementaires — UM6P.",
};

export const viewport: Viewport = {
  themeColor: "#D7492A",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans`}>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
