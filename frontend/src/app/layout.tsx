import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TanIA",
  description: "Plataforma de Agentes Inteligentes TANAC",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
