"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

const campaign = {
  id: "camp-k1m",
  title: "Kitchen Manipulation",
  banner: "/assets/logos/colored/codatta.png", // placeholder — would be a real campaign banner
  intro: "Record and annotate robotics manipulation video data for training embodied AI agents. Contributors upload kitchen task demonstration videos, which are processed by our Vision Engine for pre-labeling, then reviewed and annotated by human contributors.",
  tags: ["Robotics", "Video", "Manipulation"],
  stats: { instances: "672 / 1,000", daysLeft: 34, enrolled: 48, avgTime: "~35 min" },
  community: { contributors: 48, submittedToday: 12, avgRating: "4.7", topContributor: "contributor_8f2a" },
  tasks: [
    { type: "📤 Supply", pay: "$2.50/ea", executor: "Human", qual: { met: true, text: "✓ Qualified" } },
    { type: "🏷 Labeling", pay: "$1.50/ea", executor: "Human", qual: { met: false, text: "⚠ Complete tutorial" } },
    { type: "✅ Validation", pay: "—", executor: "Agent", qual: { met: true, text: "(automatic)" } },
  ],
  pipeline: [
    { label: "Supply", executor: "human", desc: "Upload 30–120s video" },
    { label: "Validation", executor: "agent", desc: "Quality gate" },
    { label: "Labeling", executor: "human", desc: "Annotate actions" },
    { label: "Label-Val", executor: "agent", desc: "Consistency check" },
  ],
  comp: { model: "Fixed", desc: "$2.50 per accepted supply, $1.50 per accepted labeling. Payout within 48 hours." },
  qualifications: [
    { label: "Platform: reputation ≥ 500", met: true },
    { label: "Domain: robotics experience", met: true },
    { label: "Certification: complete tutorial", met: false },
  ],
  org: { name: "NVIDIA PhysicalAI", industry: "Robotics & AI", trust: "Trusted ★ 4.8", stats: "12 campaigns · 94% on-time" },
};

export default function CampaignDetailPage() {
  const allMet = campaign.qualifications.every((q) => q.met);

  return (
    <div className="px-10 py-8 max-w-[960px]">
      {/* Back */}
      <Link href="/contribute/campaigns" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-[#1B1034] transition">
        <ArrowLeft size={14} /> Back to Campaigns
      </Link>

      {/* === HUMAN LAYER: Visual + Introduction === */}

      {/* Banner image */}
      <div className="border-[1.5px] border-[#1B1034] mt-4 h-48 bg-[#1B1034] flex items-center justify-center overflow-hidden">
        <p className="text-white text-sm">Campaign banner image</p>
      </div>

      {/* Title + intro */}
      <h1 className="text-2xl font-bold text-[#1B1034] mt-6">{campaign.title}</h1>
      <div className="flex gap-1.5 mt-2 flex-wrap">
        {campaign.tags.map((t) => (
          <span key={t} className="border border-gray-300 text-[11px] text-[#1B1034] px-2 py-0.5">{t}</span>
        ))}
      </div>
      <p className="text-sm text-[#5C5470] mt-3 leading-relaxed">{campaign.intro}</p>

      {/* === HUMAN LAYER: Community & People === */}

      <div className="border-[1.5px] border-[#1B1034] mt-8">
        <div className="px-5 py-3 border-b border-gray-200">
          <p className="text-xs font-semibold text-[#1B1034] uppercase tracking-wide">Community</p>
        </div>
        <div className="grid grid-cols-4 divide-x divide-gray-200">
          {[
            { label: "Contributors", value: String(campaign.community.contributors) },
            { label: "Submitted today", value: String(campaign.community.submittedToday) },
            { label: "Avg rating", value: campaign.community.avgRating },
            { label: "Instances", value: campaign.stats.instances },
          ].map((s) => (
            <div key={s.label} className="px-5 py-4 text-center">
              <p className="text-2xl font-bold text-[#1B1034]">{s.value}</p>
              <p className="text-[11px] text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* === DATA LAYER: Tasks, Pipeline, Compensation === */}

      {/* Task Type Breakdown */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Task Type Breakdown</h2>
      <div className="border-[1.5px] border-[#1B1034] mt-2">
        {campaign.tasks.map((t, i) => (
          <div key={t.type} className={`px-5 py-3 flex items-center justify-between ${i < campaign.tasks.length - 1 ? "border-b border-gray-200" : ""}`}>
            <span className="text-sm font-medium text-[#1B1034] w-[140px]">{t.type}</span>
            <span className="text-sm text-[#5C5470] w-[100px]">{t.pay}</span>
            <span className="text-sm text-[#5C5470] w-[80px]">{t.executor}</span>
            <span className={`text-xs font-medium ${t.qual.met ? "text-green-600" : "text-amber-600"}`}>
              {t.qual.text}
            </span>
          </div>
        ))}
      </div>

      {/* How It Works */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">How It Works</h2>
      <div className="border-[1.5px] border-[#1B1034] p-5 mt-2">
        <div className="flex items-center gap-0">
          {campaign.pipeline.map((stage, i) => (
            <div key={stage.label} className="flex items-center">
              <div className="flex flex-col items-center">
                <div className={`w-28 h-10 flex items-center justify-center text-xs font-medium border-[1.5px] ${stage.executor === "agent" ? "border-gray-300 text-[#9890A8]" : "border-[#1B1034] text-[#1B1034]"}`}>
                  {stage.label}
                </div>
                <p className="text-[10px] text-[#9890A8] mt-1.5">{stage.executor}</p>
              </div>
              {i < campaign.pipeline.length - 1 && (
                <div className="w-6 h-px bg-[#1B1034] shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Compensation */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Compensation</h2>
      <div className="border-[1.5px] border-[#1B1034] p-5 mt-2">
        <p className="text-sm font-medium text-[#1B1034]">💵 {campaign.comp.model} pay</p>
        <p className="text-sm text-[#5C5470] mt-1">{campaign.comp.desc}</p>
      </div>

      {/* Qualifications */}
      <h2 id="qualifications" className="text-sm font-semibold text-[#1B1034] mt-8">Your Qualifications</h2>
      <div className="border-[1.5px] border-[#1B1034] p-5 mt-2 space-y-2">
        {campaign.qualifications.map((q) => (
          <div key={q.label} className="flex items-center gap-2.5 text-sm">
            <span className={q.met ? "text-green-600" : "text-amber-600"}>
              {q.met ? "✓" : "⚠"}
            </span>
            <span className={q.met ? "text-[#5C5470]" : "text-[#1B1034]"}>{q.label}</span>
            {!q.met && (
              <button className="ml-auto px-3 py-1.5 bg-[#1B1034] text-white text-[11px] font-medium hover:bg-[#2D2250] transition cursor-pointer">
                Start Tutorial →
              </button>
            )}
          </div>
        ))}
      </div>

      {/* === DEVELOPER LAYER: Organization (last) === */}

      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Organization</h2>
      <div className="border-[1.5px] border-[#1B1034] p-5 mt-2 flex items-center gap-4">
        <div className="w-12 h-12 border border-[#1B1034] flex items-center justify-center text-[#1B1034] text-lg shrink-0">N</div>
        <div>
          <p className="text-sm font-semibold text-[#1B1034]">{campaign.org.name}</p>
          <p className="text-xs text-[#9890A8]">{campaign.org.industry} · {campaign.org.trust}</p>
          <p className="text-xs text-[#9890A8]">{campaign.org.stats}</p>
        </div>
      </div>

      {/* Sticky footer */}
      <div className="sticky bottom-0 bg-white border-t-[1.5px] border-[#1B1034] mt-10 -mx-10 px-10 py-4 flex items-center justify-between">
        <div>
          {allMet ? (
            <span className="text-sm text-green-600 font-medium">✓ You qualify for all tasks</span>
          ) : (
            <span className="text-sm text-amber-600 font-medium">⚠ 1 requirement not met</span>
          )}
          <p className="text-[11px] text-[#9890A8] mt-0.5">{campaign.stats.daysLeft} days left · {campaign.community.contributors} contributors enrolled</p>
        </div>
        <button
          onClick={() => {
            if (allMet) {
              if (confirm("Enroll in Kitchen Manipulation? You'll start receiving tasks immediately.")) {
                window.location.href = "/contribute/tasks";
              }
            } else {
              document.getElementById("qualifications")?.scrollIntoView({ behavior: "smooth" });
            }
          }}
          className={`px-6 py-2.5 text-sm font-medium transition cursor-pointer ${allMet ? "bg-[#1B1034] text-white hover:bg-[#2D2250]" : "border-[1.5px] border-[#1B1034] text-[#1B1034] bg-white hover:bg-gray-50"}`}
        >
          {allMet ? "Enroll Now" : "View Requirements"}
        </button>
      </div>
    </div>
  );
}
