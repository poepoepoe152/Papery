import type { Metadata } from "next";
import "./globals.css";

import { AuthProvider } from "@/lib/auth";
import { ThemeProvider } from "@/components/theme-provider";

export const metadata: Metadata = {
  title: "Papery — AI Document Verification",
  description:
    "Papery compares your business documents, detects mismatches, and generates verification reports — automatically.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
