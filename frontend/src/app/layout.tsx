import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

export const metadata: Metadata = {
  title: "Quantum Lab",
  description: "Interactive Quantum Learning Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased dark">
        {children}
      </body>
    </html>
  );
}
