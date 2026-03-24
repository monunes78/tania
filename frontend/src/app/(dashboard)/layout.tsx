import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import { AppHeader } from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { SessionProvider } from "next-auth/react";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  if (!session) redirect("/login");

  // Buscar departamentos e agentes do usuário
  // TODO: substituir por chamada real à API quando implementada
  const departments: any[] = [];
  const isAdmin = (session.user as any)?.is_admin ?? false;

  return (
    <SessionProvider session={session}>
      <div style={{ display: "flex", minHeight: "100vh" }}>
        <AppSidebar departments={departments} isAdmin={isAdmin} />
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
          <AppHeader />
          <main style={{ flex: 1, padding: "1.5rem", background: "var(--background)" }}>
            {children}
          </main>
        </div>
      </div>
    </SessionProvider>
  );
}
