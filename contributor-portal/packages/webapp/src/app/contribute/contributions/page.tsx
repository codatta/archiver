"use client";

import { useState } from "react";
import { X } from "lucide-react";

const rows = [
  { campaign: "Kitchen Manip.", type: "🏷 Lab", typeColor: "text-[#834DFB]", instance: "#inst-4f2a", chain: "0xa3b7c4d5e6f1", chainShort: "0xa3..f1", chainColor: "text-[#834DFB]", status: "✓ Accepted", statusColor: "text-green-600", progress: 100, progressColor: "bg-green-500", pay: "$1.50", submitted: "Feb 12, 2025 14:32", quality: "Grade A", lifecycle: "label_accepted", consensus: "2/3 agree" },
  { campaign: "Kitchen Manip.", type: "📤 Sup", typeColor: "text-gray-600", instance: "#inst-8b1c", chain: "0xb7e291d3a4c5", chainShort: "0xb7..e2", chainColor: "text-[#834DFB]", status: "✓ Accepted", statusColor: "text-green-600", progress: 75, progressColor: "bg-green-500", pay: "$2.50", submitted: "Feb 11, 2025 09:15", quality: "Grade B", lifecycle: "supply_accepted", consensus: "—" },
  { campaign: "RoboMIND", type: "🏷 Lab", typeColor: "text-[#834DFB]", instance: "#inst-d7e3", chain: "0xf491a2c7b8d3", chainShort: "0xf4..a2", chainColor: "text-[#834DFB]", status: "✓ Accepted", statusColor: "text-green-600", progress: 100, progressColor: "bg-green-500", pay: "royalty", submitted: "Feb 10, 2025 16:45", quality: "Grade A", lifecycle: "royalty_eligible", consensus: "3/3 agree" },
  { campaign: "Xperience", type: "🏷 Lab", typeColor: "text-[#834DFB]", instance: "#inst-b3c8", chain: "", chainShort: "—", chainColor: "text-gray-300", status: "● Working", statusColor: "text-[#834DFB]", progress: 50, progressColor: "bg-[#834DFB]", pay: "—", submitted: "Feb 13, 2025 11:20", quality: "—", lifecycle: "label_pending", consensus: "—" },
  { campaign: "Bones Motion", type: "🏷 Lab", typeColor: "text-[#834DFB]", instance: "#inst-8a1f", chain: "", chainShort: "—", chainColor: "text-gray-300", status: "✕ Rejected", statusColor: "text-red-500", progress: 25, progressColor: "bg-red-400", pay: "—", submitted: "Feb 9, 2025 13:30", quality: "Grade D", lifecycle: "label_rejected", consensus: "0/3 agree" },
  { campaign: "VLA Comm.", type: "✅ Val", typeColor: "text-gray-600", instance: "#inst-5c8a", chain: "0xd2f7a8b3c4e1", chainShort: "0xd2..a8", chainColor: "text-[#834DFB]", status: "✓ Accepted", statusColor: "text-green-600", progress: 100, progressColor: "bg-green-500", pay: "$0.50", submitted: "Feb 8, 2025 10:00", quality: "Grade A", lifecycle: "completed", consensus: "—" },
];

const columns = [
  { label: "Campaign", width: "w-[160px]" },
  { label: "Type", width: "w-[72px]" },
  { label: "Instance", width: "w-[110px]" },
  { label: "Chain ID", width: "w-[100px]" },
  { label: "Status", width: "w-[100px]" },
  { label: "Stage", width: "w-[100px]" },
  { label: "Pay", width: "w-[72px]" },
];

type Row = typeof rows[number];

function DetailDrawer({ row, onClose }: { row: Row; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      <div className="absolute inset-0 bg-[#1B1034]/30" />
      <div
        className="relative w-[480px] h-full bg-white border-l-[1.5px] border-[#1B1034] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-200 flex items-start justify-between">
          <div>
            <p className="text-base font-bold text-[#1B1034]">Instance {row.instance}</p>
            <p className="text-sm text-[#5C5470] mt-0.5">{row.campaign} · {row.type}</p>
          </div>
          <button onClick={onClose} className="text-[#9890A8] hover:text-[#1B1034] cursor-pointer">
            <X size={18} />
          </button>
        </div>

        {/* Pipeline */}
        <div className="px-6 py-4 border-b border-gray-200">
          <p className="text-[11px] font-semibold text-[#1B1034] uppercase tracking-wide">Pipeline</p>
          <div className="flex gap-[2px] mt-3 h-6">
            <div className="bg-[#1B1034] flex-[1] flex items-center justify-center text-[9px] text-white">supply</div>
            <div className="bg-[#1B1034] flex-[1] flex items-center justify-center text-[9px] text-white">validation</div>
            <div className={`flex-[2] flex items-center justify-center text-[9px] ${row.progress >= 100 ? "bg-[#1B1034] text-white" : "bg-[#834DFB] text-white"}`}>labeling</div>
            <div className={`flex-[1] flex items-center justify-center text-[9px] ${row.lifecycle === "completed" || row.lifecycle === "royalty_eligible" ? "bg-[#1B1034] text-white" : "bg-gray-200 text-[#9890A8]"}`}>label-val</div>
          </div>
        </div>

        {/* Data preview placeholder */}
        <div className="px-6 py-4 border-b border-gray-200">
          <p className="text-[11px] font-semibold text-[#1B1034] uppercase tracking-wide">Data Preview</p>
          <div className="mt-3 border-[1.5px] border-[#1B1034] h-40 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <p className="text-sm text-[#9890A8]">▶ Media preview</p>
              <p className="text-[11px] text-[#9890A8] mt-1">Video / audio / text loads here</p>
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="px-6 py-4 border-b border-gray-200">
          <p className="text-[11px] font-semibold text-[#1B1034] uppercase tracking-wide">Details</p>
          <div className="mt-3 space-y-2">
            {[
              { label: "Submitted", value: row.submitted },
              { label: "Status", value: row.status.replace(/^[✓◐●✕] /, ""), color: row.statusColor },
              { label: "Quality", value: row.quality },
              { label: "Reward", value: row.pay === "—" ? "Pending" : row.pay },
              { label: "Chain ID", value: row.chain || "Not committed", color: row.chain ? "text-[#834DFB]" : "text-[#9890A8]" },
              { label: "Lifecycle", value: row.lifecycle },
              { label: "Consensus", value: row.consensus },
            ].map((d) => (
              <div key={d.label} className="flex items-center justify-between text-sm">
                <span className="text-[#9890A8] w-[120px] shrink-0">{d.label}</span>
                <span className={`text-right ${d.color || "text-[#1B1034]"}`}>{d.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Lineage */}
        <div className="px-6 py-4">
          <p className="text-[11px] font-semibold text-[#1B1034] uppercase tracking-wide">Lineage</p>
          <div className="mt-3 space-y-1.5 text-sm">
            <p className="text-[#9890A8]">← Supply by contributor_8f2a</p>
            <p className="text-[#9890A8]">← Validation (agent) auto-pass</p>
            <p className="font-semibold text-[#1B1034]">● You: {row.type.replace(/[📤🏷✅] /, "")}</p>
            <p className="text-[#9890A8]">→ Label-validation {row.lifecycle === "completed" ? "passed" : "pending"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ContributionsPage() {
  const [selected, setSelected] = useState<Row | null>(null);

  return (
    <div className="px-10 py-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1B1034]">Contributions</h1>
          <p className="text-sm text-[#5C5470] mt-1">147 submissions across 5 campaigns</p>
        </div>
        <button className="px-4 py-2 border-[1.5px] border-[#1B1034] text-xs font-medium text-[#1B1034] bg-white hover:bg-gray-50 transition cursor-pointer">
          Export CSV ↓
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2.5 mt-5">
        {["Campaign", "Task Type", "Status", "Date range"].map((f) => (
          <select key={f} className="py-2 px-4 border-[1.5px] border-[#1B1034] bg-white text-xs text-[#1B1034] cursor-pointer">
            <option>{f}</option>
          </select>
        ))}
        <input
          placeholder="Search instance..."
          className="py-2 px-4 border-[1.5px] border-[#1B1034] bg-white text-xs text-[#1B1034] placeholder:text-gray-400 w-[180px] ml-auto outline-none focus:border-[#834DFB]"
        />
      </div>

      {/* Table */}
      <div className="border-[1.5px] border-[#1B1034] mt-4 overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b-[1.5px] border-[#1B1034]">
              {columns.map((col) => (
                <th key={col.label} className={`${col.width} text-left text-[11px] font-semibold text-[#9890A8] uppercase tracking-wide px-5 py-3`}>
                  {col.label}
                </th>
              ))}
              <th className="w-[48px]" />
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr
                key={i}
                onClick={() => setSelected(r)}
                className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition"
              >
                <td className="px-5 py-4 text-[13px] font-medium text-[#1B1034]">{r.campaign}</td>
                <td className={`px-5 py-4 text-[11px] font-medium ${r.typeColor}`}>{r.type}</td>
                <td className="px-5 py-4 text-[11px] font-mono text-[#5C5470]">{r.instance}</td>
                <td className={`px-5 py-4 text-[11px] font-mono ${r.chainColor}`}>{r.chainShort}</td>
                <td className={`px-5 py-4 text-[11px] font-medium ${r.statusColor}`}>{r.status}</td>
                <td className="px-5 py-4">
                  <div className="w-full h-1.5 bg-gray-200 overflow-hidden">
                    <div className={`h-full ${r.progressColor}`} style={{ width: `${r.progress}%` }} />
                  </div>
                </td>
                <td className="px-5 py-4 text-[13px] font-medium text-[#1B1034]">
                  {r.pay === "—" ? <span className="text-gray-300">—</span> : r.pay === "royalty" ? <span className="text-[#834DFB]">royalty</span> : r.pay}
                </td>
                <td className="px-5 py-4 text-[#9890A8] text-sm">▸</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-3">
        <span className="text-xs text-[#9890A8]">Showing 1–6 of 147</span>
        <div className="flex gap-1">
          {["← Prev", "1", "2", "3", "Next →"].map((p) => (
            <button key={p} className={`h-7 px-2.5 text-xs cursor-pointer ${p === "1" ? "bg-[#1B1034] text-white" : "border border-gray-300 bg-white hover:bg-gray-50"}`}>
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Detail drawer */}
      {selected && <DetailDrawer row={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
