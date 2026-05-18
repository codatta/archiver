"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Plus, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import {
  MOCK_CAMPAIGN,
  MOCK_SEGMENTS,
  MOCK_DRAFT_SEGMENTS,
  mockFrameForIndex,
  mockFilmstripThumbnails,
  type ActionSegmentDraft,
} from "@/lib/mock/workspace";
import { FramePlayer } from "@/components/workspace/frame-player";
import { FilmstripScrubber } from "@/components/workspace/filmstrip-scrubber";
import { useWorkspaceNav } from "@/components/workspace/nav-context";

// Annotate page — maps to labeling.codatta.io/web/annotate/:id/slice.
// Contributor fine-cuts action boundaries, assigns action labels, and writes
// language instructions + task plan per action segment.
//
// The set of draft segments begins from MOCK_DRAFT_SEGMENTS (valid segments
// that survived review). As I2-1 lands, this will read from review decisions.

export default function AnnotatePage() {
  const [drafts, setDrafts] = useState<ActionSegmentDraft[]>(MOCK_DRAFT_SEGMENTS);
  const [activeDraftIdx, setActiveDraftIdx] = useState<number>(0);
  const [currentFrameIdx, setCurrentFrameIdx] = useState<number>(
    MOCK_DRAFT_SEGMENTS[0]?.startFrame ?? 0
  );
  const { setDirty } = useWorkspaceNav();

  // Annotate progress IS draft-cacheable. Labels, language instructions, and
  // task plan steps are persisted per segment in annotations.temporal (I3-2).
  useEffect(() => {
    const withWork = drafts.filter(
      (d) => d.actionLabel || d.languageInstruction.length > 0 || d.taskPlan.length > 0
    ).length;
    setDirty({
      isDirty: withWork > 0,
      isDraftCacheable: true,
      description:
        withWork > 0
          ? `${withWork} of ${drafts.length} action segments have in-progress annotations.`
          : "",
    });
    return () => setDirty({ isDirty: false, isDraftCacheable: true, description: "" });
  }, [drafts, setDirty]);

  // selectDraft centralises activation so current-frame always snaps to the
  // new segment's start. Avoids a useEffect that fires setState in response
  // to activeDraftIdx changes (react-hooks/set-state-in-effect).
  const selectDraft = useCallback(
    (nextIdx: number) => {
      const clamped = Math.max(0, Math.min(nextIdx, drafts.length - 1));
      setActiveDraftIdx(clamped);
      setCurrentFrameIdx(drafts[clamped].startFrame);
    },
    [drafts]
  );

  const activeDraft = drafts[activeDraftIdx];
  const matchingSourceSegment = MOCK_SEGMENTS.find((s) => s.id === activeDraft?.segmentId);

  const thumbnails = useMemo(() => {
    if (!matchingSourceSegment) return [];
    return mockFilmstripThumbnails(
      matchingSourceSegment.id,
      matchingSourceSegment.frame_count,
      Math.max(1, Math.floor(matchingSourceSegment.frame_count / 12))
    ).map((t) => ({
      frame_idx: matchingSourceSegment.start_idx + t.frame_idx,
      url: t.url,
    }));
  }, [matchingSourceSegment]);

  const currentFrame = matchingSourceSegment
    ? mockFrameForIndex(
        matchingSourceSegment.id,
        currentFrameIdx - matchingSourceSegment.start_idx
      )
    : null;

  const setActionLabel = useCallback((draftIdx: number, label: string) => {
    setDrafts((prev) => {
      const next = [...prev];
      next[draftIdx] = { ...next[draftIdx], actionLabel: label };
      return next;
    });
  }, []);

  const setLanguageInstruction = useCallback((draftIdx: number, text: string) => {
    setDrafts((prev) => {
      const next = [...prev];
      next[draftIdx] = { ...next[draftIdx], languageInstruction: text };
      return next;
    });
  }, []);

  const addTaskStep = useCallback((draftIdx: number) => {
    setDrafts((prev) => {
      const next = [...prev];
      next[draftIdx] = {
        ...next[draftIdx],
        taskPlan: [...next[draftIdx].taskPlan, ""],
      };
      return next;
    });
  }, []);

  const updateTaskStep = useCallback((draftIdx: number, stepIdx: number, text: string) => {
    setDrafts((prev) => {
      const next = [...prev];
      const steps = [...next[draftIdx].taskPlan];
      steps[stepIdx] = text;
      next[draftIdx] = { ...next[draftIdx], taskPlan: steps };
      return next;
    });
  }, []);

  const removeTaskStep = useCallback((draftIdx: number, stepIdx: number) => {
    setDrafts((prev) => {
      const next = [...prev];
      const steps = next[draftIdx].taskPlan.filter((_, i) => i !== stepIdx);
      next[draftIdx] = { ...next[draftIdx], taskPlan: steps };
      return next;
    });
  }, []);

  // Keyboard shortcuts 1–5 assign action labels from campaign vocabulary.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;

      const matchingLabel = MOCK_CAMPAIGN.actionVocabulary.find(
        (l) => l.shortcut === e.key
      );
      if (matchingLabel) {
        e.preventDefault();
        setActionLabel(activeDraftIdx, matchingLabel.value);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        selectDraft(activeDraftIdx + 1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        selectDraft(activeDraftIdx - 1);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [activeDraftIdx, selectDraft, setActionLabel]);

  if (!activeDraft || !matchingSourceSegment || !currentFrame) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#111827] text-gray-400 text-sm">
        No draft segments to annotate.
      </div>
    );
  }

  const completedCount = drafts.filter((d) => d.actionLabel && d.languageInstruction).length;

  return (
    <div className="flex-1 flex flex-col bg-[#111827] overflow-hidden">
      <div className="flex-1 flex min-h-0">
        {/* Left: draft segments list */}
        <div className="w-[220px] bg-[#1F2937] border-r border-gray-700 shrink-0 flex flex-col">
          <div className="p-3 border-b border-gray-700">
            <p className="text-[10px] text-gray-400 uppercase tracking-wide font-semibold">
              Action segments
            </p>
            <p className="text-[10px] text-gray-500 mt-1">
              {drafts.length} segments carried over from review
            </p>
          </div>
          <div className="flex-1 overflow-y-auto">
            {drafts.map((draft, idx) => {
              const isActive = idx === activeDraftIdx;
              const hasLabel = !!draft.actionLabel;
              const hasLanguage = draft.languageInstruction.length > 0;
              const labelStyle = MOCK_CAMPAIGN.actionVocabulary.find(
                (l) => l.value === draft.actionLabel
              );

              return (
                <button
                  key={draft.segmentId}
                  type="button"
                  onClick={() => selectDraft(idx)}
                  className={`w-full text-left px-3 py-2.5 border-b border-gray-700 transition cursor-pointer ${
                    isActive ? "bg-[#1B1034]" : "hover:bg-gray-800"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-gray-300">{draft.segmentId}</span>
                    <div className="flex gap-1">
                      {hasLabel && (
                        <span
                          className="w-2 h-2"
                          style={{ backgroundColor: labelStyle?.background ?? "#834DFB" }}
                          aria-label="has label"
                        />
                      )}
                      {hasLanguage && (
                        <span className="w-2 h-2 bg-green-500" aria-label="has language" />
                      )}
                    </div>
                  </div>
                  <p className="text-[10px] text-gray-500 mt-0.5 font-mono">
                    frames {draft.startFrame}–{draft.endFrame}
                  </p>
                  {draft.actionLabel && (
                    <p
                      className="text-[10px] mt-1 font-medium"
                      style={{ color: labelStyle?.background ?? "#ffffff" }}
                    >
                      {draft.actionLabel}
                    </p>
                  )}
                </button>
              );
            })}
          </div>
          <div className="border-t border-gray-700 p-3 bg-[#111827]">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-gray-400">Complete</span>
              <span className="text-gray-200 font-mono">
                {completedCount} / {drafts.length}
              </span>
            </div>
            <div className="mt-1.5 h-1 bg-gray-700 overflow-hidden">
              <div
                className="h-full bg-[#22C55E] transition-all"
                style={{
                  width: `${(completedCount / drafts.length) * 100}%`,
                }}
              />
            </div>
          </div>
        </div>

        {/* Center: frame player + language + task plan */}
        <div className="flex-1 flex flex-col overflow-y-auto bg-[#374151]">
          <div className="flex items-center justify-center p-4 shrink-0">
            <div className="flex flex-col items-center gap-3">
              <FramePlayer
                frameUrl={null}
                bbox={currentFrame.person_bbox}
                keypoints={currentFrame.arm_keypoints}
                width={640}
                frameIdx={currentFrameIdx}
              />
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => selectDraft(activeDraftIdx - 1)}
                  disabled={activeDraftIdx === 0}
                  className="w-8 h-8 bg-[#1B1034] text-white flex items-center justify-center hover:bg-[#2D2250] transition cursor-pointer disabled:opacity-30"
                  aria-label="Previous action segment"
                >
                  <ChevronLeft size={16} />
                </button>
                <p className="text-[11px] text-gray-400 font-mono">
                  segment {activeDraftIdx + 1} / {drafts.length} · {activeDraft.segmentId}
                </p>
                <button
                  type="button"
                  onClick={() => selectDraft(activeDraftIdx + 1)}
                  disabled={activeDraftIdx === drafts.length - 1}
                  className="w-8 h-8 bg-[#1B1034] text-white flex items-center justify-center hover:bg-[#2D2250] transition cursor-pointer disabled:opacity-30"
                  aria-label="Next action segment"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          </div>

          {/* Language instruction + task plan */}
          <div className="bg-[#111827] border-t border-gray-700 p-5 space-y-5">
            <div>
              <label
                htmlFor="languageInstruction"
                className="text-[10px] text-gray-400 uppercase tracking-wide font-semibold block mb-2"
              >
                Language instruction
              </label>
              <textarea
                id="languageInstruction"
                value={activeDraft.languageInstruction}
                onChange={(e) => setLanguageInstruction(activeDraftIdx, e.target.value)}
                placeholder="Describe what the person is doing in this segment…"
                rows={2}
                className="w-full bg-[#1F2937] border-[1.5px] border-gray-700 focus:border-[#834DFB] text-sm text-white px-3 py-2 resize-none focus:outline-none"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-[10px] text-gray-400 uppercase tracking-wide font-semibold">
                  Task plan — ordered steps
                </label>
                <button
                  type="button"
                  onClick={() => addTaskStep(activeDraftIdx)}
                  className="flex items-center gap-1 text-[10px] text-[#834DFB] hover:text-[#9B6DFF] transition cursor-pointer"
                >
                  <Plus size={12} />
                  Add step
                </button>
              </div>
              {activeDraft.taskPlan.length === 0 ? (
                <p className="text-[11px] text-gray-500 italic py-2">
                  No steps yet. Click &ldquo;Add step&rdquo; to plan out the high-level actions.
                </p>
              ) : (
                <ol className="space-y-2">
                  {activeDraft.taskPlan.map((step, stepIdx) => (
                    <li key={stepIdx} className="flex gap-2 items-start">
                      <span className="text-[11px] font-mono text-gray-500 pt-2 w-5 shrink-0">
                        {stepIdx + 1}.
                      </span>
                      <input
                        type="text"
                        value={step}
                        onChange={(e) =>
                          updateTaskStep(activeDraftIdx, stepIdx, e.target.value)
                        }
                        placeholder="e.g. pick up towel"
                        className="flex-1 bg-[#1F2937] border-[1.5px] border-gray-700 focus:border-[#834DFB] text-sm text-white px-3 py-1.5 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => removeTaskStep(activeDraftIdx, stepIdx)}
                        className="w-8 h-8 text-gray-500 hover:text-red-400 flex items-center justify-center transition cursor-pointer"
                        aria-label="Remove step"
                      >
                        <Trash2 size={14} />
                      </button>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        </div>

        {/* Right: action label palette */}
        <div className="w-[220px] bg-[#1F2937] border-l border-gray-700 shrink-0 flex flex-col">
          <div className="p-3 border-b border-gray-700">
            <p className="text-[10px] text-gray-400 uppercase tracking-wide font-semibold">
              Action label
            </p>
            <p className="text-[10px] text-gray-500 mt-1 leading-relaxed">
              Assign one label to the active segment. Keyboard shortcuts{" "}
              <kbd className="text-gray-300">1</kbd>–<kbd className="text-gray-300">5</kbd>.
            </p>
          </div>
          <div className="flex-1 p-2 space-y-1.5 overflow-y-auto">
            {MOCK_CAMPAIGN.actionVocabulary.map((label) => {
              const isSelected = activeDraft.actionLabel === label.value;
              return (
                <button
                  key={label.value}
                  type="button"
                  onClick={() => setActionLabel(activeDraftIdx, label.value)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition cursor-pointer border-[1.5px] ${
                    isSelected ? "bg-white" : "bg-[#111827] hover:bg-gray-800 border-transparent"
                  }`}
                  style={{
                    borderColor: isSelected ? label.background : undefined,
                  }}
                >
                  <span
                    className="w-3 h-3 shrink-0"
                    style={{ backgroundColor: label.background }}
                  />
                  <span
                    className={`text-xs font-mono flex-1 ${isSelected ? "text-[#1B1034] font-semibold" : "text-gray-300"}`}
                  >
                    {label.value}
                  </span>
                  <kbd
                    className={`text-[10px] px-1.5 py-0.5 ${
                      isSelected
                        ? "bg-[#1B1034] text-white"
                        : "bg-gray-700 text-gray-400"
                    }`}
                  >
                    {label.shortcut}
                  </kbd>
                </button>
              );
            })}
          </div>
          <div className="border-t border-gray-700 p-3 text-[10px] text-gray-500">
            Bounding box editing (I3-1) and keypoint correction (I3-1) plug into FramePlayer in a
            later iteration.
          </div>
        </div>
      </div>

      {/* Bottom: filmstrip */}
      <FilmstripScrubber
        thumbnails={thumbnails}
        currentFrameIdx={currentFrameIdx}
        onSelectFrame={setCurrentFrameIdx}
      />
    </div>
  );
}
