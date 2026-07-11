import type { Metadata } from "next";
import "./globals.css";
import { AppLayout } from "../components/AppLayout";

export const metadata: Metadata = {
  title: "PoC Renovater",
  description: "AI-powered PoC development platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`antialiased`}>
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
