"use client";

import { useState } from "react";
import Image from "next/image";
import { StepIndicator } from "@/components/auth/step-indicator";
import { BRAND } from "@/lib/config";

type Step = 1 | 2 | 3;

const skills = [
  "Robotics Annotation",
  "NLP / LLM Evaluation",
  "Computer Vision",
  "Data Collection",
  "Audio Transcription",
  "Medical Imaging",
];

const taskTypes = [
  {
    id: "supply",
    icon: "📤",
    label: "Supply",
    desc: "Record videos, upload files, capture data",
  },
  {
    id: "labeling",
    icon: "🏷",
    label: "Labeling",
    desc: "Review AI outputs, label segments, add text",
  },
  {
    id: "validation",
    icon: "✅",
    label: "Validation",
    desc: "Grade quality, verify accuracy, approve/reject",
  },
];

const timeOptions = ["< 5 hrs", "5–15 hrs", "15–30 hrs", "30+ hrs"];

export default function OnboardingPage() {
  const [step, setStep] = useState<Step>(1);
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set());
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [timeCommitment, setTimeCommitment] = useState<string | null>(null);

  function toggleSkill(skill: string) {
    setSelectedSkills((prev) => {
      const next = new Set(prev);
      if (next.has(skill)) next.delete(skill);
      else next.add(skill);
      return next;
    });
  }

  function toggleType(id: string) {
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-[480px]">
        {/* Logo */}
        <Image
          src={BRAND.logo}
          alt={BRAND.name}
          width={36}
          height={36}
          className="w-9 h-9"
        />

        {/* Step 1: Skills */}
        {step === 1 && (
          <>
            <h1 className="text-[22px] font-semibold text-[#1B1034] mt-6">
              What are you good at?
            </h1>
            <p className="text-[13px] text-gray-500 mt-1">
              Select skills relevant to data contribution work. You can update
              these later.
            </p>

            <div className="mt-5 mb-6">
              <StepIndicator steps={3} current={1} />
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              {skills.map((skill) => {
                const selected = selectedSkills.has(skill);
                return (
                  <button
                    key={skill}
                    onClick={() => toggleSkill(skill)}
                    className={`p-3.5 text-left text-[13px] font-medium transition cursor-pointer ${
                      selected
                        ? "border-[1.5px] border-[#1B1034] bg-[#F0EBFF] text-[#1B1034]"
                        : "border border-gray-200 text-gray-700 hover:border-[#1B1034]"
                    }`}
                  >
                    {selected && (
                      <span className="text-[#834DFB] mr-1.5">✓</span>
                    )}
                    {skill}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => setStep(2)}
              disabled={selectedSkills.size === 0}
              className="w-full py-2.5 mt-6 bg-[#1B1034] text-white text-[13px] font-medium hover:bg-[#2D2250] transition disabled:opacity-50 cursor-pointer"
            >
              Continue
            </button>

            <button
              onClick={() => setStep(2)}
              className="block w-full text-center text-[13px] text-gray-400 hover:text-gray-600 mt-3"
            >
              Skip for now
            </button>
          </>
        )}

        {/* Step 2: Interests */}
        {step === 2 && (
          <>
            <h1 className="text-[22px] font-semibold text-[#1B1034] mt-6">
              What kind of work interests you?
            </h1>
            <p className="text-[13px] text-gray-500 mt-1">
              This helps us recommend campaigns.
            </p>

            <div className="mt-5 mb-6">
              <StepIndicator steps={3} current={2} />
            </div>

            <p className="text-[13px] font-medium text-[#1B1034] mb-2.5">
              Preferred task types
            </p>
            <div className="flex flex-col gap-2.5">
              {taskTypes.map((t) => {
                const selected = selectedTypes.has(t.id);
                return (
                  <button
                    key={t.id}
                    onClick={() => toggleType(t.id)}
                    className={`p-3.5 text-left transition cursor-pointer ${
                      selected
                        ? "border-[1.5px] border-[#1B1034] bg-[#F0EBFF]"
                        : "border border-gray-200 hover:border-[#1B1034]"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {selected && (
                        <span className="text-[#834DFB] text-sm">✓</span>
                      )}
                      <span className="text-[13px] font-medium text-[#1B1034]">
                        {t.icon} {t.label}
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-500 mt-0.5 ml-5">
                      {t.desc}
                    </p>
                  </button>
                );
              })}
            </div>

            <p className="text-[13px] font-medium text-[#1B1034] mt-5 mb-2.5">
              How much time per week?
            </p>
            <div className="grid grid-cols-4 gap-0 border border-[#1B1034]">
              {timeOptions.map((opt) => (
                <button
                  key={opt}
                  onClick={() => setTimeCommitment(opt)}
                  className={`py-2 text-[11px] font-medium transition cursor-pointer ${
                    timeCommitment === opt
                      ? "bg-[#1B1034] text-white"
                      : "bg-white text-gray-600 hover:bg-gray-50"
                  } ${opt !== timeOptions[0] ? "border-l border-[#1B1034]" : ""}`}
                >
                  {opt}
                </button>
              ))}
            </div>

            <button
              onClick={() => setStep(3)}
              className="w-full py-2.5 mt-6 bg-[#1B1034] text-white text-[13px] font-medium hover:bg-[#2D2250] transition cursor-pointer"
            >
              Continue
            </button>

            <button
              onClick={() => setStep(3)}
              className="block w-full text-center text-[13px] text-gray-400 hover:text-gray-600 mt-3"
            >
              Skip for now
            </button>
          </>
        )}

        {/* Step 3: Ready */}
        {step === 3 && (
          <>
            <h1 className="text-[22px] font-semibold text-[#1B1034] mt-6">
              You&apos;re all set!
            </h1>
            <p className="text-[13px] text-gray-500 mt-1">
              Your profile is ready. Start exploring campaigns.
            </p>

            <div className="mt-5 mb-6">
              <StepIndicator steps={3} current={3} />
            </div>

            {/* Profile preview */}
            <div className="border-[1.5px] border-[#1B1034] p-6 text-center">
              <div className="w-16 h-16 bg-[#1B1034] rounded-full flex items-center justify-center mx-auto">
                <span className="text-xl font-semibold text-white">YZ</span>
              </div>
              <p className="text-lg font-semibold text-[#1B1034] mt-3">
                Yi Zhang
              </p>
              <p className="text-[13px] text-[#834DFB]">@yi_zhang</p>
              {selectedSkills.size > 0 && (
                <p className="text-[12px] text-gray-500 mt-2">
                  Skills: {[...selectedSkills].join(", ")}
                </p>
              )}
              {(selectedTypes.size > 0 || timeCommitment) && (
                <p className="text-[12px] text-gray-500 mt-1">
                  {selectedTypes.size > 0 &&
                    `Interests: ${[...selectedTypes].join(", ")}`}
                  {selectedTypes.size > 0 && timeCommitment && " · "}
                  {timeCommitment && `${timeCommitment}/week`}
                </p>
              )}
            </div>

            <p className="text-[13px] font-medium text-[#1B1034] mt-6 mb-2">
              What to do next:
            </p>
            <ol className="text-[13px] text-gray-600 space-y-1 list-decimal pl-5">
              <li>Browse campaigns and find work that fits your skills</li>
              <li>Enroll in a campaign to start receiving tasks</li>
              <li>Complete tasks to earn and build reputation</li>
            </ol>

            <button
              onClick={() => (window.location.href = "/contribute/discover")}
              className="w-full py-2.5 mt-6 bg-[#1B1034] text-white text-[13px] font-medium hover:bg-[#2D2250] transition cursor-pointer"
            >
              Discover Campaigns →
            </button>

            <button
              onClick={() => (window.location.href = "/contribute")}
              className="block w-full text-center text-[13px] text-[#834DFB] hover:underline mt-3"
            >
              Go to Dashboard
            </button>
          </>
        )}

        {/* Footer */}
        <p className="text-[11px] text-gray-400 text-center mt-10">
          &copy; 2026 Codatta PTE LTD.
        </p>
      </div>
    </div>
  );
}
