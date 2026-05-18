"use client";

import { useState, useRef, useEffect } from "react";
import { Upload, FileVideo, Settings2, ChevronDown } from "lucide-react";
import { MOCK_CAMPAIGN } from "@/lib/mock/workspace";
import { useWorkspaceNav } from "@/components/workspace/nav-context";

type UploadedFile = {
  name: string;
  size: number;
  type: "video" | "sequence";
};

export default function SupplyPage() {
  const [file, setFile] = useState<UploadedFile | null>(null);
  const [presetId, setPresetId] = useState<string>(MOCK_CAMPAIGN.detectionPresets[1].id);
  const [taskName, setTaskName] = useState<string>("");
  const [scenarioCode, setScenarioCode] = useState<string>("SCENE_01");
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { setDirty } = useWorkspaceNav();

  const selectedPreset = MOCK_CAMPAIGN.detectionPresets.find((p) => p.id === presetId);

  // Supply is NOT draft-cacheable until the file is uploaded to Supabase
  // Storage (I1-2). Until then, leaving discards the selection.
  useEffect(() => {
    const dirty = file !== null || taskName.length > 0;
    setDirty({
      isDirty: dirty,
      isDraftCacheable: false,
      description: file
        ? `You have "${file.name}" selected but haven't uploaded it yet.`
        : "You've started filling in metadata but haven't uploaded a file.",
    });
    return () => setDirty({ isDirty: false, isDraftCacheable: true, description: "" });
  }, [file, taskName, setDirty]);

  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    const f = files[0];
    const isZip = f.name.endsWith(".zip");
    setFile({
      name: f.name,
      size: f.size,
      type: isZip ? "sequence" : "video",
    });
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  return (
    <div className="flex-1 flex flex-col bg-[#F5F5F3] overflow-y-auto">
      <div className="max-w-[880px] w-full mx-auto px-8 py-10">
        <header className="mb-8">
          <p className="text-xs font-semibold text-[#834DFB] uppercase tracking-wide">
            Step 1 of 4 — Data Supply
          </p>
          <h1 className="text-2xl font-bold text-[#1B1034] mt-1">Upload your capture</h1>
          <p className="text-sm text-[#5C5470] mt-1">
            Upload a single video (MP4, MOV) or a ZIP of image sequences. Vision Engine will
            segment the footage and identify informative clips before you review.
          </p>
        </header>

        {/* File upload area */}
        <section className="mb-8">
          <label className="text-xs font-semibold text-[#1B1034] uppercase tracking-wide mb-2 block">
            File
          </label>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-[1.5px] border-dashed ${
              isDragging ? "border-[#834DFB] bg-[#F0EBFF]" : "border-[#1B1034] bg-white"
            } p-10 flex flex-col items-center justify-center cursor-pointer transition`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="video/mp4,video/quicktime,.zip"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
            {file ? (
              <>
                <FileVideo size={40} className="text-[#834DFB]" />
                <p className="text-sm font-medium text-[#1B1034] mt-3">{file.name}</p>
                <p className="text-xs text-[#5C5470] mt-1">
                  {(file.size / 1024 / 1024).toFixed(1)} MB · {file.type}
                </p>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="mt-3 text-xs text-[#5C5470] hover:text-[#1B1034] underline cursor-pointer"
                >
                  Choose different file
                </button>
              </>
            ) : (
              <>
                <Upload size={32} className="text-[#5C5470]" />
                <p className="text-sm font-medium text-[#1B1034] mt-3">
                  Drop a file or click to browse
                </p>
                <p className="text-xs text-[#5C5470] mt-1">
                  MP4 / MOV video, or ZIP archive of image sequences
                </p>
              </>
            )}
          </div>
        </section>

        {/* Detection preset selector */}
        <section className="mb-8">
          <label className="text-xs font-semibold text-[#1B1034] uppercase tracking-wide mb-2 block">
            Detection Preset
          </label>
          <p className="text-xs text-[#5C5470] mb-3">
            Presets tune Vision Engine parameters for your capture type. Pick the closest match.
          </p>
          <div className="grid grid-cols-2 gap-3">
            {MOCK_CAMPAIGN.detectionPresets.map((preset) => {
              const isSelected = preset.id === presetId;
              return (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => setPresetId(preset.id)}
                  className={`border-[1.5px] p-4 text-left transition cursor-pointer ${
                    isSelected
                      ? "border-[#1B1034] bg-[#1B1034] text-white"
                      : "border-[#1B1034] bg-white text-[#1B1034] hover:bg-[#F0EBFF]"
                  }`}
                  aria-pressed={isSelected}
                >
                  <p className="text-sm font-semibold">{preset.name}</p>
                  <p
                    className={`text-xs mt-1 leading-relaxed ${
                      isSelected ? "text-gray-200" : "text-[#5C5470]"
                    }`}
                  >
                    {preset.description}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Advanced toggle */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="mt-3 flex items-center gap-1.5 text-xs text-[#5C5470] hover:text-[#1B1034] transition cursor-pointer"
          >
            <Settings2 size={12} />
            Advanced parameters
            <ChevronDown
              size={12}
              className={`transition-transform ${showAdvanced ? "rotate-180" : ""}`}
            />
          </button>

          {showAdvanced && selectedPreset && (
            <div className="mt-3 border-[1.5px] border-[#1B1034] bg-white p-4">
              <p className="text-xs font-semibold text-[#1B1034] mb-2">
                Parameters for {selectedPreset.name}
              </p>
              <div className="grid grid-cols-2 gap-x-6 gap-y-2">
                {Object.entries(selectedPreset.params).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-[#5C5470] font-mono">{key}</span>
                    <span className="text-[#1B1034] font-mono font-medium">{String(value)}</span>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-[#9890A8] mt-3">
                Per-parameter editing will land with I1-1 (ML Backend Adapter).
              </p>
            </div>
          )}
        </section>

        {/* Metadata form */}
        <section className="mb-8">
          <label className="text-xs font-semibold text-[#1B1034] uppercase tracking-wide mb-3 block">
            Metadata
          </label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="taskName"
                className="text-xs text-[#5C5470] mb-1.5 block"
              >
                Task name
              </label>
              <input
                id="taskName"
                type="text"
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
                placeholder="e.g. kitchen_fold_demo"
                className="w-full h-10 px-3 text-sm border-[1.5px] border-[#1B1034] bg-white text-[#1B1034] focus:outline-none focus:border-[#834DFB]"
              />
            </div>
            <div>
              <label
                htmlFor="scenarioCode"
                className="text-xs text-[#5C5470] mb-1.5 block"
              >
                Scenario code
              </label>
              <input
                id="scenarioCode"
                type="text"
                value={scenarioCode}
                onChange={(e) => setScenarioCode(e.target.value)}
                className="w-full h-10 px-3 text-sm border-[1.5px] border-[#1B1034] bg-white text-[#1B1034] focus:outline-none focus:border-[#834DFB]"
              />
            </div>
          </div>
        </section>

        {/* Status banner */}
        <div className="border-[1.5px] border-[#1B1034] bg-white px-5 py-4">
          <p className="text-xs font-semibold text-[#1B1034] mb-1">What happens next</p>
          <ol className="text-xs text-[#5C5470] space-y-1 list-decimal pl-4">
            <li>Your file uploads to Supabase Storage and a T1 instance is recorded.</li>
            <li>
              Vision Engine processes it using the{" "}
              <span className="font-semibold text-[#1B1034]">
                {selectedPreset?.name ?? "selected"}
              </span>{" "}
              preset — this can take 1–5 minutes.
            </li>
            <li>
              You&apos;ll land on <span className="font-mono">/review</span> to cull the segments
              Vision Engine flagged as uninformative.
            </li>
            <li>
              Then <span className="font-mono">/annotate</span> for slicing, action labels, and
              language instructions.
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
}
