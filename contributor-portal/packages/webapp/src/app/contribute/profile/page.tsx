"use client";

import { useState } from "react";
import Link from "next/link";

type Tab = "overview" | "credentials" | "contributions" | "settings";

const credentials = [
  { skill: "Robotics Annotation", tier: "tutorial-passed", action: "View Training", bg: "bg-[#F0EBFF]", text: "text-[#834DFB]", accent: "border-l-[3px] border-[#834DFB]" },
  { skill: "Data Collection", tier: "credential-verified", action: "View Credential", bg: "bg-green-50", text: "text-green-700", accent: "border-l-[3px] border-green-500" },
  { skill: "AI/ML Labeling", tier: "unverified", action: "Start Training →", bg: "bg-gray-100", text: "text-[#9890A8]", accent: "border-l-[3px] border-gray-300", primary: true },
];

const recentActivity = [
  { icon: "✓", text: "T3 annotation accepted · Embodiment-X", time: "2h ago", color: "text-green-600" },
  { icon: "$", text: "$12.50 earned · Kitchen Task Recording", time: "1d ago", color: "text-[#1B1034]" },
  { icon: "✕", text: "T1 upload rejected · Warehouse Nav", time: "2d ago", color: "text-red-500" },
  { icon: "↑", text: "Enrolled in RoboMIND Trajectories", time: "3d ago", color: "text-[#834DFB]" },
];

const tabs: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "credentials", label: "Credentials" },
  { id: "contributions", label: "Contributions" },
  { id: "settings", label: "Settings" },
];

export default function ProfilePage() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="px-10 py-8 max-w-[960px]">

      {/* ═══ HERO: Avatar + Name + Badges ═══ */}
      <div className="flex items-center gap-6">
        <div className="w-20 h-20 bg-[#1B1034] rounded-full flex items-center justify-center shrink-0">
          <span className="text-2xl font-bold text-white">YZ</span>
        </div>
        <div>
          <h1 className="text-2xl font-bold text-[#1B1034]">Yi Zhang</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-sm text-[#834DFB] font-medium">@yi_zhang</span>
            <span className="text-sm text-[#9890A8]">·</span>
            <span className="text-sm text-[#5C5470]">yi@humanbased.io</span>
            <span className="text-xs text-green-600">✓ Verified</span>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[11px] font-medium text-[#1B1034] border border-[#1B1034] px-2 py-0.5">Contributor</span>
            <span className="text-[11px] font-medium text-[#834DFB] border border-[#834DFB] px-2 py-0.5">Expert</span>
            <span className="text-[11px] text-[#9890A8]">Member since Dec 2024</span>
          </div>
        </div>
        <div className="ml-auto">
          <Link
            href="/contribute/settings"
            className="px-4 py-2 border-[1.5px] border-[#1B1034] text-[13px] font-medium text-[#1B1034] hover:bg-gray-50 transition"
          >
            Edit Profile
          </Link>
        </div>
      </div>

      {/* ═══ TAB BAR ═══ */}
      <div className="flex items-center gap-5 mt-8 border-b border-gray-200">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`text-sm pb-2.5 transition cursor-pointer ${
              tab === t.id
                ? "font-semibold text-[#1B1034] border-b-[2px] border-[#1B1034] -mb-px"
                : "text-[#9890A8] hover:text-[#1B1034]"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ═══ TAB CONTENT ═══ */}

      {/* Overview */}
      {tab === "overview" && (
        <div className="mt-6">
          {/* Metric cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="border-[1.5px] border-[#1B1034] p-5">
              <p className="text-xs text-[#9890A8]">Reputation</p>
              <div className="flex items-baseline gap-2 mt-1">
                <p className="text-3xl font-bold text-[#1B1034]">847</p>
                <p className="text-sm text-[#9890A8]">/ 1,000</p>
              </div>
              <div className="w-full h-1.5 bg-gray-200 mt-3 overflow-hidden">
                <div className="h-full bg-[#834DFB]" style={{ width: "84.7%" }} />
              </div>
            </div>
            <div className="border-[1.5px] border-[#1B1034] p-5">
              <p className="text-xs text-[#9890A8]">Total Earned</p>
              <p className="text-3xl font-bold text-[#1B1034] mt-1">$847.20</p>
              <p className="text-xs text-[#9890A8] mt-3">$42.50 pending</p>
            </div>
            <div className="border-[1.5px] border-[#1B1034] p-5">
              <p className="text-xs text-[#9890A8]">Contributions</p>
              <p className="text-3xl font-bold text-[#1B1034] mt-1">142</p>
              <p className="text-xs text-[#9890A8] mt-3">3 campaigns active</p>
            </div>
          </div>

          {/* Recent activity */}
          <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Recent Activity</h2>
          <div className="border-[1.5px] border-[#1B1034] mt-2">
            {recentActivity.map((a, i) => (
              <div key={i} className={`px-5 py-3 flex items-center justify-between ${i < recentActivity.length - 1 ? "border-b border-gray-200" : ""}`}>
                <div className="flex items-center gap-3">
                  <span className={`text-sm font-medium w-4 text-center ${a.color}`}>{a.icon}</span>
                  <span className="text-sm text-[#1B1034]">{a.text}</span>
                </div>
                <span className="text-xs text-[#9890A8] shrink-0">{a.time}</span>
              </div>
            ))}
          </div>

          {/* Skills snapshot */}
          <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Skills</h2>
          <div className="flex gap-2 mt-2">
            {credentials.map((c) => (
              <div key={c.skill} className={`flex items-center gap-2 border-[1.5px] border-[#1B1034] px-3 py-2 ${c.accent}`}>
                <span className="text-[13px] font-medium text-[#1B1034]">{c.skill}</span>
                <span className={`text-[10px] font-medium px-1.5 py-0.5 ${c.bg} ${c.text}`}>{c.tier}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Credentials */}
      {tab === "credentials" && (
        <div className="mt-6">
          <div className="border-[1.5px] border-[#1B1034]">
            {credentials.map((c, i) => (
              <div key={c.skill} className={`px-5 py-4 flex items-center justify-between ${c.accent} ${i < credentials.length - 1 ? "border-b border-gray-200" : ""}`}>
                <div>
                  <p className="text-sm font-medium text-[#1B1034]">{c.skill}</p>
                  <span className={`text-[11px] font-medium px-2 py-0.5 mt-1 inline-block ${c.bg} ${c.text}`}>{c.tier}</span>
                </div>
                <button className={`px-4 py-2 text-[13px] font-medium transition cursor-pointer ${
                  c.primary
                    ? "bg-[#1B1034] text-white hover:bg-[#2D2250]"
                    : "border-[1.5px] border-[#1B1034] text-[#1B1034] bg-white hover:bg-gray-50"
                }`}>
                  {c.action}
                </button>
              </div>
            ))}
          </div>

          <div className="border-[1.5px] border-[#1B1034] p-6 mt-6 text-center">
            <p className="text-sm text-[#9890A8]">Complete more credentials to unlock higher-tier campaigns</p>
            <Link href="/contribute/discover" className="text-sm font-medium text-[#834DFB] hover:underline mt-2 inline-block">
              Browse campaigns with requirements →
            </Link>
          </div>
        </div>
      )}

      {/* Contributions (quick view — links to full table) */}
      {tab === "contributions" && (
        <div className="mt-6">
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Total", value: "142", color: "text-[#1B1034]" },
              { label: "Accepted", value: "118", color: "text-green-600" },
              { label: "In Review", value: "16", color: "text-[#F59E0B]" },
              { label: "Rejected", value: "8", color: "text-red-500" },
            ].map((m) => (
              <div key={m.label} className="border-[1.5px] border-[#1B1034] p-4 text-center">
                <p className={`text-2xl font-bold mt-1 ${m.color}`}>{m.value}</p>
                <p className="text-xs text-[#9890A8] mt-1">{m.label}</p>
              </div>
            ))}
          </div>

          <Link
            href="/contribute/contributions"
            className="mt-6 w-full py-3 border-[1.5px] border-[#1B1034] text-sm font-medium text-[#1B1034] hover:bg-gray-50 transition flex items-center justify-center"
          >
            View Full Contributions Table →
          </Link>
        </div>
      )}

      {/* Settings (redirect) */}
      {tab === "settings" && (
        <div className="mt-6">
          <p className="text-sm text-[#5C5470]">Manage your account settings, avatar, and preferences.</p>
          <Link
            href="/contribute/settings"
            className="mt-4 px-5 py-2.5 bg-[#1B1034] text-white text-sm font-medium hover:bg-[#2D2250] transition inline-block"
          >
            Go to Settings →
          </Link>
        </div>
      )}
    </div>
  );
}
