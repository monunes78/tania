import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import { AppHeader } from "@/components/app-header";
import { AppSidebar } from "@/components/app-sidebar";
import { SessionProvider } from "next-auth/react";

interface AgentSummary {
  id: string;
  name: string;
}

interface DepartmentSummary {
  id: string;
  name: string;
  slug: string;
  icon: string;
  agents: AgentSummary[];
}

async function getDepartments(accessToken: string): Promise<DepartmentSummary[]> {
  const apiUrl = process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://backend:8000";
  try {
    const res = await fetch(`${apiUrl}/api/v1/me/departments`, {
      headers: {
        Cookie: `access_token=${accessToken}`,
      },
      next: { revalidate: 60 }, // cache 60s
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  if (!session) redirect("/login");

  const isAdmin = (session.user as { is_admin?: boolean })?.is_admin ?? false;
  const accessToken = (session.user as { access_token?: string })?.access_token ?? "";

  const departments = await getDepartments(accessToken);

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
