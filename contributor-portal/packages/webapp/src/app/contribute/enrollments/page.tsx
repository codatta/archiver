"use client";

import { useState } from "react";
import Link from "next/link";

const active = [
  {
    id: "camp-k1m",
    title: "Kitchen Manipulation",
    tasks: "Supply $2.50 · Labeling $1.50 · Fixed",
    submitted: 23, accepted: 18, review: 5, progress: 78,
    contributors: 48,
    earned: "$34.50",
    rank: "Top 15%",
    daysLeft: 34,
  },
  {
    id: "camp-rmnd",
    title: "RoboMIND Trajectories",
    tasks: "Supply (royalty) · Labeling (royalty) · Royalty",
    submitted: 12, accepted: 9, review: 3, progress: 75,
    contributors: 112,
    earned: "$16.20 (royalty)",
    rank: "Top 30%",
    daysLeft: 186,
  },
];

const past = [
  { id: "camp-wh", title: "Warehouse Navigation", status: "Completed", count: 47, earned: "$70.50" },
  { id: "camp-aq", title: "Assembly Line QC", status: "Ended", count: 12, earned: "$18.00" },
];

export default function EnrollmentsPage() {
  const [unenrollModal, setUnenrollModal] = useState<string | null>(null);
  const modalCampaign = active.find((e) => e.id === unenrollModal);

  return (
    <div className="px-10 py-8 max-w-[1200px]">
      <h1 className="text-2xl font-bold text-[#1B1034]">Enrollments</h1>
      <p className="text-sm text-[#5C5470] mt-1">Manage your campaign commitments</p>

      {/* Active */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Active ({active.length})</h2>
      <div className="flex flex-col gap-4 mt-3">
        {active.map((e) => (
          <Link
            key={e.id}
            href={`/contribute/campaigns/${e.id}`}
            className="border-[1.5px] border-[#1B1034] bg-white transition hover:bg-gray-50 block"
          >
            {/* Header: title + status */}
            <div className="px-5 pt-5 pb-3">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-[#1B1034]">{e.title}</h3>
                <span className="text-[11px] font-medium text-[#1B1034] border border-[#1B1034] px-2 py-0.5">Active · {e.daysLeft}d left</span>
              </div>
              <p className="text-xs text-[#9890A8] mt-1">{e.contributors} contributors enrolled</p>
            </div>

            {/* Your contribution stats — primary */}
            <div className="px-5 pb-3 border-t border-gray-200 pt-3">
              <div className="flex gap-8">
                <div>
                  <p className="text-xs text-[#9890A8]">Your Earnings</p>
                  <p className="text-lg font-bold text-[#1B1034] mt-0.5">{e.earned}</p>
                </div>
                <div>
                  <p className="text-xs text-[#9890A8]">Submitted</p>
                  <p className="text-lg font-bold text-[#1B1034] mt-0.5">{e.submitted}</p>
                </div>
                <div>
                  <p className="text-xs text-[#9890A8]">Accepted</p>
                  <p className="text-lg font-bold text-green-600 mt-0.5">{e.accepted}</p>
                </div>
                <div>
                  <p className="text-xs text-[#9890A8]">Rank</p>
                  <p className="text-lg font-bold text-[#834DFB] mt-0.5">{e.rank}</p>
                </div>
              </div>
            </div>

            {/* Progress bar + secondary info */}
            <div className="px-5 pb-3 border-t border-gray-200 pt-3">
              <p className="text-xs text-[#5C5470]">{e.tasks}</p>
              <div className="w-full h-1 bg-gray-200 mt-2 overflow-hidden">
                <div className="h-full bg-[#1B1034]" style={{ width: `${e.progress}%` }} />
              </div>
              <p className="text-[11px] text-[#9890A8] mt-1">{e.progress}% accepted · {e.review} in review</p>
            </div>

            {/* Actions — stop propagation so clicks don't navigate */}
            <div
              className="px-5 pb-4 pt-3 border-t border-gray-200 flex justify-end gap-3"
              onClick={(ev) => ev.preventDefault()}
            >
              <Link
                href={`/contribute/tasks#cg-${e.title.replace(/\s/g, "-")}`}
                className="px-5 py-2 bg-[#1B1034] text-white text-[13px] font-medium flex items-center hover:bg-[#2D2250] transition"
                onClick={(ev) => ev.stopPropagation()}
              >
                Continue Tasks
              </Link>
              <button
                onClick={(ev) => { ev.stopPropagation(); ev.preventDefault(); setUnenrollModal(e.id); }}
                className="px-5 py-2 border-[1.5px] border-[#1B1034] text-[#1B1034] text-[13px] font-medium bg-white hover:bg-gray-50 transition cursor-pointer"
              >
                Unenroll
              </button>
            </div>
          </Link>
        ))}
      </div>

      {/* Past */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-10">Past</h2>
      <div className="border-[1.5px] border-[#1B1034] mt-2">
        {past.map((p, i) => (
          <Link
            key={p.id}
            href={`/contribute/campaigns/${p.id}`}
            className={`px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition ${i < past.length - 1 ? "border-b border-gray-200" : ""}`}
          >
            <div>
              <span className="text-sm font-medium text-[#1B1034]">{p.title}</span>
              <span className="text-xs text-[#9890A8] ml-3">{p.status} · {p.count} tasks</span>
            </div>
            <span className="text-sm font-medium text-[#1B1034]">{p.earned}</span>
          </Link>
        ))}
      </div>

      {/* Unenroll confirmation modal */}
      {unenrollModal && modalCampaign && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={() => setUnenrollModal(null)}>
          <div className="absolute inset-0 bg-[#1B1034]/30" />
          <div
            className="relative bg-white border-[1.5px] border-[#1B1034] w-full max-w-[420px] p-6"
            onClick={(ev) => ev.stopPropagation()}
          >
            <h3 className="text-lg font-bold text-[#1B1034]">Unenroll from {modalCampaign.title}?</h3>

            <div className="mt-4 space-y-2 text-sm text-[#5C5470]">
              <p>This will:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Stop assigning new tasks from this campaign</li>
                <li><strong className="text-[#1B1034]">In-progress tasks will remain visible</strong> in My Tasks until you complete or cancel them</li>
                <li>Completed tasks and earnings are preserved</li>
                <li>Once all claimed tasks are resolved, this campaign will move to Past</li>
              </ul>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setUnenrollModal(null)}
                className="px-5 py-2 border-[1.5px] border-[#1B1034] text-[#1B1034] text-[13px] font-medium bg-white hover:bg-gray-50 transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => { setUnenrollModal(null); alert(`Unenrolled from ${modalCampaign.title}. In-progress tasks remain in My Tasks.`); }}
                className="px-5 py-2 bg-red-600 text-white text-[13px] font-medium hover:bg-red-700 transition cursor-pointer"
              >
                Unenroll
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
