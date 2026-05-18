"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";

type Instance = {
  id: string;
  campaignId: string;
  campaign: string;
  type: "supply" | "labeling" | "validation";
  desc: string;
  time: string;
  pay: string;
  taskId: string;
  priority?: "resume" | "expiring" | "dispute";
};

const allInstances: Instance[] = [
  // Resume: 3
  { id: "#inst-47", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Review 12 clips from kitchen demo", time: "~45 min", pay: "$1.50", taskId: "t3-label-47", priority: "resume" },
  { id: "#inst-91", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "labeling", desc: "Classify task type for trajectory", time: "~30 min", pay: "royalty", taskId: "t2-label-91", priority: "resume" },
  { id: "#inst-33", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "supply", desc: "Record 15-min daily activity", time: "~20 min", pay: "$1.00", taskId: "t1-supply-33", priority: "resume" },
  // Expiring: 5
  { id: "#inst-201", campaignId: "camp-bone", campaign: "Humanoid Motion", type: "labeling", desc: "Write motion description", time: "~20 min", pay: "bounty", taskId: "t3-label-201", priority: "expiring" },
  { id: "#inst-202", campaignId: "camp-bone", campaign: "Humanoid Motion", type: "labeling", desc: "Temporal segmentation", time: "~25 min", pay: "bounty", taskId: "t4-label-202", priority: "expiring" },
  { id: "#inst-203", campaignId: "camp-bone", campaign: "Humanoid Motion", type: "supply", desc: "Upload mocap recording", time: "~15 min", pay: "bounty", taskId: "t1-supply-203", priority: "expiring" },
  { id: "#inst-204", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Add language instructions", time: "~30 min", pay: "$1.50", taskId: "t3-label-204", priority: "expiring" },
  { id: "#inst-205", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "supply", desc: "Upload kitchen task video", time: "~15 min", pay: "$2.50", taskId: "t1-supply-205", priority: "expiring" },
  // Dispute: 2
  { id: "#inst-88", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Disputed grade — respond to reviewer feedback", time: "~10 min", pay: "$1.50", taskId: "t3-dispute-88", priority: "dispute" },
  { id: "#inst-89", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "validation", desc: "Disputed validation — reviewer disagrees", time: "~15 min", pay: "royalty", taskId: "t3-dispute-89", priority: "dispute" },
  // C1: Kitchen Manipulation — 5 available
  { id: "#inst-55", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "supply", desc: "Upload kitchen task video", time: "~15 min", pay: "$2.50", taskId: "t1-supply-55" },
  { id: "#inst-56", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "supply", desc: "Upload kitchen task video", time: "~15 min", pay: "$2.50", taskId: "t1-supply-56" },
  { id: "#inst-48", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Annotate action segments", time: "~45 min", pay: "$1.50", taskId: "t3-label-48" },
  { id: "#inst-49", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Review bounding boxes", time: "~40 min", pay: "$1.50", taskId: "t3-label-49" },
  { id: "#inst-50", campaignId: "camp-k1m", campaign: "Kitchen Manipulation", type: "labeling", desc: "Add language instructions", time: "~30 min", pay: "$1.50", taskId: "t3-label-50" },
  // C2: RoboMIND Trajectories — 4 available
  { id: "#inst-301", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "supply", desc: "Record humanoid demo", time: "~20 min", pay: "royalty", taskId: "t1-supply-301" },
  { id: "#inst-302", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "labeling", desc: "Classify task type", time: "~30 min", pay: "royalty", taskId: "t2-label-302" },
  { id: "#inst-303", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "labeling", desc: "Tag object classes", time: "~25 min", pay: "royalty", taskId: "t2-label-303" },
  { id: "#inst-304", campaignId: "camp-rmnd", campaign: "RoboMIND Trajectories", type: "validation", desc: "Verify trajectory label", time: "~15 min", pay: "royalty", taskId: "t3-val-304" },
  // C3: Egocentric Experience — 7 available
  { id: "#inst-401", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "supply", desc: "Record 15-min cooking activity", time: "~20 min", pay: "$1.00", taskId: "t1-supply-401" },
  { id: "#inst-402", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "supply", desc: "Record 15-min cleaning activity", time: "~20 min", pay: "$1.00", taskId: "t1-supply-402" },
  { id: "#inst-403", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "labeling", desc: "Hierarchical language annotation", time: "~35 min", pay: "$0.50", taskId: "t3-label-403" },
  { id: "#inst-404", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "labeling", desc: "Temporal segmentation boundaries", time: "~30 min", pay: "$0.75", taskId: "t4-label-404" },
  { id: "#inst-405", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "labeling", desc: "Activity segment annotation", time: "~25 min", pay: "$0.50", taskId: "t3-label-405" },
  { id: "#inst-406", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "validation", desc: "Verify language descriptions", time: "~15 min", pay: "$0.25", taskId: "t5-val-406" },
  { id: "#inst-407", campaignId: "camp-xp10", campaign: "Egocentric Experience", type: "validation", desc: "Check segment boundaries", time: "~15 min", pay: "$0.25", taskId: "t5-val-407" },
];

const typeLabel: Record<string, string> = { supply: "📤 Supply", labeling: "🏷 Labeling", validation: "✅ Validation" };
const typeBg: Record<string, string> = { supply: "bg-[#1B1034]", labeling: "bg-[#834DFB]", validation: "bg-[#22C55E]" };
const statusLabel: Record<string, { text: string; color: string }> = {
  resume: { text: "● In Progress", color: "text-[#1B1034]" },
  expiring: { text: "⚠ Expiring", color: "text-[#F59E0B]" },
  dispute: { text: "✕ Disputed", color: "text-red-500" },
};

// Each task type enters the workspace pipeline at a different step:
//   supply     → /supply      (upload + detection presets — T1)
//   labeling   → /review      (cull review is the first human step after VE pre-label — T3a)
//   validation → /review      (validators inspect the same timeline; their decisions write to T4 in I5-1)
// Resume priority: the URL still points to the starting step; in I0-4 this will
// read `task_instances.status` and deep-link to the exact in-progress step.
const typeToStep: Record<Instance["type"], "supply" | "review" | "annotate" | "export"> = {
  supply: "supply",
  labeling: "review",
  validation: "review",
};

function workspaceHref(inst: Instance): string {
  return `/workspace/${inst.campaignId}/${inst.taskId}/${typeToStep[inst.type]}`;
}

const resumeCount = allInstances.filter((i) => i.priority === "resume").length;
const expiringCount = allInstances.filter((i) => i.priority === "expiring").length;
const disputeCount = allInstances.filter((i) => i.priority === "dispute").length;

// Fixed-size task card — same everywhere
function TaskCard({ inst }: { inst: Instance }) {
  // Generate a deterministic pattern seed from instance id
  const seed = inst.id.charCodeAt(inst.id.length - 1) % 5;
  const patterns = [
    "from-gray-100 to-gray-200",
    "from-gray-50 to-gray-150",
    "from-gray-100 to-gray-50",
    "from-gray-200 to-gray-100",
    "from-gray-50 to-gray-200",
  ];

  return (
    <Link
      href={workspaceHref(inst)}
      className="w-[320px] h-[260px] border-[1.5px] border-[#1B1034] bg-white flex flex-col transition hover:bg-gray-50 shrink-0 max-[400px]:w-full"
    >
      {/* Image / preview area */}
      <div className={`h-[110px] bg-gradient-to-br ${patterns[seed]} flex items-center justify-center relative`}>
        <div className={`w-8 h-8 ${typeBg[inst.type]} flex items-center justify-center`}>
          <span className="text-white text-[10px]">▶</span>
        </div>
      </div>

      {/* Content — fixed space */}
      <div className="flex-1 px-3 pt-2.5 pb-3 flex flex-col">
        <p className="text-[12px] font-medium text-[#1B1034] line-clamp-2 leading-tight">{inst.desc}</p>

        <div className="mt-auto">
          <p className="text-[10px] text-[#5C5470]">
            {typeLabel[inst.type]} · {inst.time}
          </p>
          <p className="text-[10px] text-[#9890A8] mt-0.5">
            {inst.pay === "royalty" || inst.pay === "bounty" ? (
              <span className="text-[#834DFB]">{inst.pay}</span>
            ) : (
              inst.pay
            )}
            {" · "}
            {inst.campaign}
          </p>

          {inst.priority && (
            <p className={`text-[10px] font-medium mt-1 ${statusLabel[inst.priority].color}`}>
              {statusLabel[inst.priority].text}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}

const available = allInstances.filter((i) => !i.priority);
const campaigns = [...new Set(available.map((i) => i.campaign))];
const grouped: Record<string, Instance[]> = {};
for (const inst of available) {
  if (!grouped[inst.campaign]) grouped[inst.campaign] = [];
  grouped[inst.campaign].push(inst);
}

export default function TasksPage() {
  const [expandedPriority, setExpandedPriority] = useState<string | null>(null);
  const [activeCampaign, setActiveCampaign] = useState<string | null>(campaigns[0] || null);
  const [isTabStuck, setIsTabStuck] = useState(false);
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);
  const tabBarRef = useRef<HTMLDivElement>(null);
  const isClickScrolling = useRef(false);

  // Sticky detection
  useEffect(() => {
    const el = tabBarRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => setIsTabStuck(!entry.isIntersecting),
      { threshold: [1], rootMargin: "-57px 0px 0px 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Sync active campaign tab with scroll position
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (isClickScrolling.current) return;
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const rawName = entry.target.id.replace("cg-", "").replace(/-/g, " ");
            const match = campaigns.find((c) => c.replace(/\s/g, " ").toLowerCase() === rawName.toLowerCase());
            if (match) setActiveCampaign(match);
          }
        }
      },
      { threshold: 0.3, rootMargin: "-80px 0px -50% 0px" }
    );
    campaigns.forEach((c) => {
      const el = document.getElementById(`cg-${c.replace(/\s/g, "-")}`);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  const priorityInstances = expandedPriority
    ? allInstances.filter((i) => i.priority === expandedPriority)
    : [];

  const isExpanded = expandedPriority !== null;

  function handleCampaignClick(name: string) {
    setActiveCampaign(name);
    isClickScrolling.current = true;
    document.getElementById(`cg-${name.replace(/\s/g, "-")}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    setTimeout(() => { isClickScrolling.current = false; }, 800);
  }

  // Render campaign tabs into topbar when stuck
  useEffect(() => {
    const slot = document.getElementById("topbar-left-slot");
    if (!slot) return;
    if (isTabStuck) {
      slot.setAttribute("data-has-tabs", "true");
    } else {
      slot.removeAttribute("data-has-tabs");
    }
  }, [isTabStuck]);

  return (
    <div>
      {/* SECTION 1: Today */}
      <div className="px-8 pt-8 pb-10">
        <h1 className="text-2xl font-bold text-[#1B1034]">My Tasks</h1>
        <div className="border-[1.5px] border-[#1B1034] px-5 py-3 flex gap-8 items-center mt-4">
          <span className="text-sm font-semibold text-[#1B1034]">Today:</span>
          <span className="text-sm text-[#5C5470]">7 submitted</span>
          <span className="text-sm text-green-600">$18.50 earned</span>
          <span className="text-sm text-red-500">2 rejected</span>
        </div>
      </div>

      {/* SECTION 2: Priority Items */}
      <div className="px-8 pb-10">
        <p className="text-sm font-semibold text-[#1B1034]">Priority Items</p>

      {/* Priority block */}
      {(() => {
        const tiles = [
          { id: "resume", label: "Resume", count: resumeCount },
          { id: "expiring", label: "Expiring Soon", count: expiringCount },
          { id: "dispute", label: "In Dispute", count: disputeCount },
        ];
        const activeIndex = tiles.findIndex((t) => t.id === expandedPriority);

        return (
          <div className="mt-2 transition-all duration-300 ease-out">
            {/* Tiles row */}
            <div className="flex gap-4">
              {tiles.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setExpandedPriority(expandedPriority === p.id ? null : p.id)}
                  className={`flex-1 aspect-[5/3] flex flex-col items-center justify-center text-white transition cursor-pointer ${
                    expandedPriority === p.id
                      ? "bg-[#2D2250]"
                      : "bg-[#1B1034] hover:bg-[#2D2250]"
                  }`}
                >
                  <span className="text-3xl font-bold">{p.count}</span>
                  <span className="text-[11px] font-medium opacity-70 mt-1">{p.label}</span>
                </button>
              ))}
            </div>

            {/* Connector + carousel stripe */}
            <div
              className="overflow-hidden transition-all duration-300 ease-out"
              style={{ maxHeight: isExpanded ? "340px" : "0px" }}
            >
              {/* L / T / flipped-L connector — same width as tile */}
              {activeIndex >= 0 && (
                <div className="flex gap-4 h-4">
                  {tiles.map((_, i) => (
                    <div key={i} className={`flex-1 ${i === activeIndex ? "bg-[#1B1034]" : ""}`} />
                  ))}
                </div>
              )}

              {/* Black stripe with task cards + view-more arrow */}
              <div
                className="bg-[#1B1034] flex overflow-hidden"
                style={{
                  opacity: isExpanded ? 1 : 0,
                  transform: isExpanded ? "scale(1) translateY(0)" : "scale(0.96) translateY(-10px)",
                  transition: "opacity 0.25s ease-out 0.1s, transform 0.25s ease-out 0.1s",
                }}
              >
                {/* Cards area — scrollable */}
                <div className="flex-1 flex gap-5 overflow-x-auto p-5">
                  {priorityInstances.map((inst) => (
                    <TaskCard key={inst.id} inst={inst} />
                  ))}
                </div>

                {/* View-more stripe — right edge */}
                <div className="w-14 bg-[#2D2250] flex items-center justify-center shrink-0 cursor-pointer hover:bg-[#3D3260] transition">
                  <span className="text-white text-2xl">›</span>
                </div>
              </div>
            </div>
          </div>
        );
      })()}
      </div>

      {/* SECTION 3: Enrolled Campaign Tasks */}
      <div ref={tabBarRef}>

        {/* Campaign selector — merges into topbar on scroll */}
        <div
          className={`bg-white z-10 sticky top-[54px] flex gap-0 transition-all duration-200 ${
            isTabStuck
              ? "px-8 py-1.5"
              : "px-8 py-3"
          }`}
        >
          {campaigns.map((c, i) => {
            const isActive = activeCampaign === c;
            const isHovered = hoveredTab === c;
            const showFull = isHovered || isActive;
            return (
              <button
                key={c}
                onClick={() => handleCampaignClick(c)}
                onMouseEnter={() => setHoveredTab(c)}
                onMouseLeave={() => setHoveredTab(null)}
                className={`text-[11px] font-medium py-1.5 cursor-pointer whitespace-nowrap overflow-hidden border-[1.5px] border-[#1B1034] transition-all duration-200 ${
                  i > 0 ? "-ml-[1.5px]" : ""
                } ${isActive ? "bg-[#1B1034] text-white z-10 relative" : isHovered ? "bg-[#2D2250] text-white z-10 relative" : "bg-white text-[#1B1034]"}`}
                style={{
                  maxWidth: showFull ? "260px" : "100px",
                  paddingLeft: showFull ? "12px" : "8px",
                  paddingRight: showFull ? "12px" : "8px",
                  transition: "max-width 0.25s ease, padding 0.2s ease, background-color 0.15s, color 0.15s",
                }}
              >
                {c}
              </button>
            );
          })}
        </div>

      {/* Campaign sections — timeline with alternating backgrounds */}
      {(() => {
        const entries = Object.entries(grouped);
        const total = entries.length;

        return (
          <div className="mt-2 -mx-8">
            {entries.map(([campaign, insts], idx) => {
              const isGray = idx % 2 === 0;
              const isFirst = idx === 0;
              const isLast = idx === total - 1;
              const campaignId = insts[0]?.campaignId || "";

              return (
                <div
                  key={campaign}
                  id={`cg-${campaign.replace(/\s/g, "-")}`}
                  className={isGray ? "bg-[#F5F5F3]" : "bg-white"}
                >
                  <div className="px-12 flex">
                    {/* Timeline column — line + node aligned to title */}
                    <div className="w-3 shrink-0 relative">
                      {/* Continuous line — top half hidden for first, bottom half hidden for last */}
                      {!isFirst && <div className="absolute top-0 left-1/2 -translate-x-1/2 w-px bg-[#1B1034]" style={{ height: "calc(1.25rem + 6px)" }} />}
                      {!isLast && <div className="absolute left-1/2 -translate-x-1/2 w-px bg-[#1B1034] bottom-0" style={{ top: "calc(1.25rem + 6px + 12px)" }} />}
                      {/* Node — vertically centered on the title line (pt-5 = 1.25rem, title ~20px, center = 1.25rem + 6px) */}
                      <div className="absolute left-0 w-3 h-3 bg-[#1B1034] rounded-full" style={{ top: "calc(1.25rem + 3px)" }} />
                    </div>

                    {/* Content column */}
                    <div className="flex-1 pl-3 min-w-0">
                      {/* Campaign header */}
                      <div className="flex items-center gap-3 pt-5">
                        <span className="text-base font-bold text-[#1B1034]">{campaign}</span>
                        <Link
                          href={`/contribute/campaigns/${campaignId}`}
                          className="text-[11px] text-[#9890A8] hover:text-[#1B1034] transition"
                        >
                          View details →
                        </Link>
                      </div>

                      {/* Cards grid */}
                      <div className="flex flex-wrap gap-6 pt-4 pb-8">
                        {insts.map((inst) => (
                          <TaskCard key={inst.id} inst={inst} />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        );
      })()}

      <p className="text-xs text-[#9890A8] text-center py-10">— no more tasks —</p>
      </div>
    </div>
  );
}
