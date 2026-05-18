import React, { useEffect, useState } from "react";
import { navigate } from "../../App";
import { apiFetch } from "../../lib/api";
import { THEME } from "../../lib/config";

type Props = { orgId: string };

const CARDS = [
  {
    title: "Browse available datasets",
    description: "Subscribe to data verticals to start receiving structured data.",
    image: "/images/onboarding/subscriptions.png",
    path: "/dashboard/subscriptions",
    buttonLabel: "Go to Subscriptions",
  },
  {
    title: "Create your first API key",
    description: "Generate API keys to authenticate your data requests.",
    image: "/images/onboarding/api-keys.png",
    path: "/dashboard/api-keys",
    buttonLabel: "Go to API Keys",
  },
] as const;

export function StepNextActions({ orgId }: Props) {
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch(`/v1/onboarding/complete?org_id=${orgId}`, { method: "POST" })
      .then(() => setCompleted(true))
      .catch((e) => setError(e.message));
  }, [orgId]);

  if (error) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-red-500">{error}</p>
        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          className="px-5 py-2.5 text-white rounded-none text-sm font-medium"
          style={{ background: THEME.btnBg }}
        >
          Continue to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[#1B1034] mb-1">You're all set!</h2>
        <p className="text-sm" style={{ color: THEME.textSecondary }}>
          Choose what you'd like to do next.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {CARDS.map((card) => (
          <button
            key={card.path}
            type="button"
            onClick={() => navigate(card.path)}
            className="group text-left rounded-none overflow-hidden hover:shadow-lg transition-shadow"
            style={{ border: `${THEME.borderWidth} solid ${THEME.border}` }}
          >
            <div className="aspect-[4/3] overflow-hidden bg-gray-50">
              <img
                src={card.image}
                alt={card.title}
                className="w-full h-full object-cover object-top group-hover:scale-[1.02] transition-transform"
              />
            </div>
            <div className="p-5 space-y-2">
              <h3 className="text-sm font-bold" style={{ color: THEME.textPrimary }}>
                {card.title}
              </h3>
              <p className="text-xs" style={{ color: THEME.textSecondary }}>
                {card.description}
              </p>
              <span
                className="inline-block mt-2 text-xs font-semibold"
                style={{ color: THEME.accent }}
              >
                {card.buttonLabel} &rarr;
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
