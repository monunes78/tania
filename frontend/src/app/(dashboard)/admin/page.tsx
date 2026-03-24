import Link from "next/link";

const adminCards = [
  {
    href: "/admin/departments",
    icon: "🏢",
    title: "Departamentos",
    description: "Gerencie departamentos e grupos de acesso AD",
  },
  {
    href: "/admin/agents",
    icon: "🤖",
    title: "Agentes",
    description: "Configure agentes de IA por departamento",
  },
  {
    href: "/admin/llm",
    icon: "⚡",
    title: "Configurações LLM",
    description: "Gerencie provedores e modelos de linguagem",
  },
];

export default function AdminPage() {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Admin Panel</h1>
        <p className="text-muted-foreground mt-1">
          Configurações e gestão da plataforma TanIA
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {adminCards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="block p-5 rounded-lg border border-border bg-card hover:border-primary/50 hover:shadow-sm transition-all"
          >
            <div className="text-3xl mb-3">{card.icon}</div>
            <h2 className="font-semibold text-foreground mb-1">{card.title}</h2>
            <p className="text-sm text-muted-foreground">{card.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
