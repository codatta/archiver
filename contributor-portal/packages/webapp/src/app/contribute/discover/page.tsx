import Link from "next/link";

const campaigns = [
  { id: "camp-k1m", org: "NVIDIA PhysicalAI", orgTier: "Open", title: "Kitchen Manipulation", desc: "Record and annotate robotics manipulation videos for embodied AI training.", tags: ["Robotics", "Video", "Manipulation"], tasks: "📤 Supply ($2.50) · 🏷 Labeling ($1.50) · ✅ Agent", comp: "💵 Fixed · $2.50/instance", stats: "672 / 1,000 instances · 34 days left", contributors: 48, qual: { status: "qualified" as const, text: "✓ You qualify" } },
  { id: "camp-rmnd", org: "Verified AI Company", orgTier: "Shielded", title: "RoboMIND Trajectories", desc: "107K real-world humanoid robot demonstration trajectories spanning 479 tasks.", tags: ["Humanoid", "Trajectories", "Real-world"], tasks: "📤 Supply (royalty) · 🏷 Labeling (royalty) · ✅ Validation (royalty)", comp: "📈 Royalty · est. $1.80/ea", stats: "23,400 / 107,000 instances · 186 days left", contributors: 112, qual: { status: "qualified" as const, text: "✓ You qualify" } },
  { id: "camp-xp10", org: "Ropedia AI", orgTier: "Open", title: "Egocentric Experience", desc: "First-person recordings with depth, audio, and mocap for spatial intelligence.", tags: ["Egocentric", "Multi-modal", "Spatial"], tasks: "📤 Supply ($1.00) · 🏷 Labeling ($0.50) · ✅ Validation ($0.25)", comp: "🔀 Hybrid · $1.00 + royalty", stats: "1.2M / 10M instances · 365 days left", contributors: 340, qual: { status: "partial" as const, text: "⚠ 1 req not met" } },
  { id: "camp-bone", org: "Technology Company", orgTier: "Guarded", title: "Humanoid Motion Library", desc: "142K annotated human motion animations for humanoid robotics retargeting.", tags: ["Motion Capture", "Animation", "Humanoid"], tasks: "📤 Supply (bounty) · 🏷 Labeling (bounty) · ✅ Agent", comp: "🎯 Bounty · $5,000 milestone", stats: "89,400 / 142,220 instances · 62 days left", contributors: 87, qual: { status: "not_qualified" as const, text: "✕ 2 reqs not met" } },
];

export default function DiscoverPage() {
  return (
    <div className="px-10 py-8 max-w-[1200px]">
      <h1 className="text-2xl font-bold text-[#1B1034]">Discover</h1>
      <p className="text-sm text-[#5C5470] mt-1">Find campaigns and start earning</p>

      {/* Filters */}
      <div className="flex items-center gap-2.5 mt-5 flex-wrap">
        {["Frontier", "Pay", "Task Type", "Qualified", "Sort"].map((f) => (
          <select key={f} className="py-2 px-4 border-[1.5px] border-[#1B1034] bg-white text-xs text-[#1B1034] cursor-pointer">
            <option>{f}</option>
          </select>
        ))}
        <span className="text-xs text-[#9890A8] ml-auto">{campaigns.length} campaigns</span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 gap-5 mt-5">
        {campaigns.map((c) => (
          <Link
            key={c.id}
            href={`/contribute/campaigns/${c.id}`}
            className={`bg-white border-[1.5px] border-[#1B1034] transition ${c.qual.status === "not_qualified" ? "opacity-50" : "hover:border-[#834DFB]"}`}
          >
            {/* HUMAN: Title + description + contributors */}
            <div className="px-5 pt-5 pb-4">
              <h3 className="text-[15px] font-bold text-[#1B1034] line-clamp-1">{c.title}</h3>
              <p className="text-[13px] text-[#5C5470] mt-1 line-clamp-2">{c.desc}</p>
              <div className="flex items-center gap-3 mt-3">
                <span className="text-[11px] text-[#1B1034] font-medium">{c.contributors} contributors</span>
                <span className="text-[11px] text-[#9890A8]">{c.stats}</span>
              </div>
            </div>

            {/* DATA: Tags + tasks + compensation */}
            <div className="px-5 pb-4 border-t border-gray-200 pt-3">
              <div className="flex gap-1.5 flex-wrap">
                {c.tags.map((t) => (
                  <span key={t} className="border border-gray-300 text-[11px] text-[#1B1034] px-2 py-0.5">{t}</span>
                ))}
              </div>
              <p className="text-[11px] text-[#5C5470] mt-2">{c.tasks}</p>
              <p className="text-[11px] font-medium text-[#1B1034] mt-1.5">{c.comp}</p>
            </div>

            {/* DEVELOPER: Org + qualification */}
            <div className="px-5 pb-4 pt-3 border-t border-gray-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 border border-[#1B1034] flex items-center justify-center text-[10px] text-[#9890A8] shrink-0">
                  {c.orgTier === "Guarded" ? "?" : c.orgTier === "Shielded" ? "◆" : c.org.charAt(0)}
                </div>
                <span className="text-[11px] text-[#9890A8]">{c.org}</span>
              </div>
              <span className={`text-[11px] font-medium ${c.qual.status === "qualified" ? "text-green-600" : c.qual.status === "partial" ? "text-amber-600" : "text-[#9890A8]"}`}>
                {c.qual.text}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
