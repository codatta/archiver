"use client";

// FilmstripScrubber — horizontal frame thumbnail strip for scrubbing.
// Reference: labeling-website FilmstripScrubber. Uses a clip+segment model;
// keyframes (action segment start/end) render as split markers between thumbs.

type FilmstripThumbnail = {
  frame_idx: number;
  url: string | null;
};

type SplitMarker = {
  after_frame_idx: number;
  label?: string;
};

type FilmstripScrubberProps = {
  thumbnails: FilmstripThumbnail[];
  currentFrameIdx: number;
  onSelectFrame: (frame_idx: number) => void;
  splitMarkers?: SplitMarker[];
  onSplit?: (after_frame_idx: number) => void;
};

export function FilmstripScrubber({
  thumbnails,
  currentFrameIdx,
  onSelectFrame,
  splitMarkers = [],
  onSplit,
}: FilmstripScrubberProps) {
  return (
    <div className="bg-[#1F2937] border-t border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <p className="text-[10px] text-gray-400 uppercase tracking-wide font-semibold">
          Filmstrip — drag to split, click to jump
        </p>
        <p className="text-[10px] text-gray-400 font-mono">
          frame {currentFrameIdx} / {thumbnails[thumbnails.length - 1]?.frame_idx ?? 0}
        </p>
      </div>
      <div className="flex gap-0.5 overflow-x-auto pb-1">
        {thumbnails.map((thumb, i) => {
          const isCurrent = thumb.frame_idx === currentFrameIdx;
          const isSplit = splitMarkers.some((m) => m.after_frame_idx === thumb.frame_idx);

          return (
            <div key={thumb.frame_idx} className="flex items-center shrink-0">
              <button
                type="button"
                onClick={() => onSelectFrame(thumb.frame_idx)}
                onDoubleClick={() => onSplit?.(thumb.frame_idx)}
                className={`w-16 h-10 flex items-center justify-center text-[9px] font-mono transition cursor-pointer ${
                  isCurrent
                    ? "bg-[#834DFB] text-white ring-2 ring-[#834DFB] ring-offset-1 ring-offset-[#1F2937]"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
                title={`Frame ${thumb.frame_idx}. Double-click to split after this frame.`}
              >
                {thumb.frame_idx}
              </button>
              {isSplit && i < thumbnails.length - 1 && (
                <div className="w-0.5 h-12 bg-[#FFEAA7] mx-0.5" aria-label="split marker" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
