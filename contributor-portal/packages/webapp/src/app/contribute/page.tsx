import Link from "next/link";

const metrics = [
  { label: "Total Earned", value: "$847.20", color: "text-[#1B1034]" },
  { label: "Active Campaigns", value: "3", color: "text-[#1B1034]" },
  { label: "Completed", value: "142", color: "text-[#1B1034]" },
  { label: "Pending", value: "$42.50", color: "text-[#F59E0B]" },
];

const alerts = [
  { icon: "⏳", text: "4 labeled instances stuck in queue — Embodiment-X · no movement 6 days" },
  { icon: "🔚", text: "Kitchen Task Recording ending in 3 days — 8 instances remaining" },
  { icon: "✕", text: "T1 upload rejected — Warehouse Navigation", danger: true },
];

const actions = [
  { title: "Continue Tasks →", desc: "8 instances ready across 2 campaigns", href: "/contribute/tasks", primary: true },
  { title: "Discover Campaigns →", desc: "5 new campaigns matching your skills", href: "/contribute/discover", primary: false },
  { title: "View Earnings →", desc: "$42.50 pending payout", href: "/contribute/earnings", primary: false },
];

export default function DashboardPage() {
  return (
    <div className="px-10 py-8 max-w-[1200px]">
      <h1 className="text-2xl font-semibold text-[#1B1034]">
        Good morning, Yi
      </h1>

      {/* Metrics */}
      <div className="grid grid-cols-4 gap-4 mt-6">
        {metrics.map((m) => (
          <div key={m.label} className="bg-white border-[1.5px] border-[#1B1034] p-5">
            <p className="text-xs text-gray-500">{m.label}</p>
            <p className={`text-4xl font-bold mt-1 ${m.color}`}>
              {m.value}
            </p>
          </div>
        ))}
      </div>

      {/* Attention */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">
        Needs Attention
      </h2>
      <div className="bg-white border-[1.5px] border-[#1B1034] divide-y divide-gray-100 mt-2">
        {alerts.map((a, i) => (
          <div key={i} className="px-5 py-4 flex items-start gap-2.5 text-sm">
            <span className={a.danger ? "text-red-500" : ""}>{a.icon}</span>
            <span className="text-gray-600">{a.text}</span>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">
        Quick Actions
      </h2>
      <div className="grid grid-cols-3 gap-4 mt-2">
        {actions.map((a) => (
          <Link
            key={a.title}
            href={a.href}
            className={`bg-white p-5 transition hover:border-[#1B1034] ${
              a.primary
                ? "border-[1.5px] border-[#1B1034]"
                : "border-[1.5px] border-[#1B1034]"
            }`}
          >
            <p className="text-sm font-semibold text-[#1B1034]">{a.title}</p>
            <p className="text-xs text-gray-400 mt-1">{a.desc}</p>
          </Link>
        ))}
      </div>

      {/* Recent Activity */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">
        Recent Activity
      </h2>
      <div className="divide-y divide-gray-100 mt-2">
        <p className="text-sm text-gray-500 py-2">
          ✓ T3 annotation accepted · Embodiment-X · 2h ago
        </p>
        <p className="text-sm text-gray-500 py-2">
          $ $12.50 earned · Kitchen Task Recording · 1d ago
        </p>
        <p className="text-sm text-gray-500 py-2">
          ✕ T1 upload rejected · Warehouse Nav · 2d ago
        </p>
      </div>
    </div>
  );
}
