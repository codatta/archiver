import React, { useState } from "react";
import { navigate } from "../App";
import { BRAND, THEME } from "../lib/config";
import { StepOrgDetails } from "../components/onboarding/StepOrgDetails";
import { StepInviteMembers } from "../components/onboarding/StepInviteMembers";
import { StepNextActions } from "../components/onboarding/StepNextActions";

const STEPS = ["Organization", "Invite Team", "Get Started"] as const;

export function Onboarding() {
  const [step, setStep] = useState(0);
  const [orgId, setOrgId] = useState<string | null>(null);

  return (
    <div className="min-h-screen" style={{ background: THEME.bg }}>
      <header style={{ background: THEME.surface, borderBottom: `1.5px solid ${THEME.border}` }}>
        <div className="max-w-6xl mx-auto flex items-center px-8 h-14">
          <img src={BRAND.logo} alt={BRAND.name} className="h-8 w-auto" />
        </div>
      </header>
      <div className={`mx-auto pt-12 px-4 ${step === 2 ? "max-w-2xl" : "max-w-lg"}`}>
        <h1 className="text-2xl font-semibold text-[#1B1034] mb-4">Set up your organization</h1>
        <div className="flex items-center gap-2 mb-8">
          {STEPS.map((label, i) => (
            <React.Fragment key={label}>
              {i > 0 && <span className="text-gray-300 text-sm">&rarr;</span>}
              <div className="flex items-center gap-1.5">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${i <= step ? "bg-[#1B1034] text-white" : "border border-gray-300 text-gray-400"}`}>
                  {i < step ? "\u2713" : i + 1}
                </div>
                <span className={`text-sm ${i <= step ? "font-medium text-[#1B1034]" : "text-gray-400"}`}>{label}</span>
              </div>
            </React.Fragment>
          ))}
        </div>
        {step === 0 && <StepOrgDetails onCreated={(id) => { setOrgId(id); setStep(1); }} onSkipped={() => navigate("/dashboard")} />}
        {step === 1 && orgId && <StepInviteMembers orgId={orgId} onDone={() => setStep(2)} />}
        {step === 2 && orgId && <StepNextActions orgId={orgId} />}
      </div>
    </div>
  );
}
