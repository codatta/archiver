"use client";

import { useState, useEffect } from "react";

export function useResendCooldown(seconds: number) {
  const [remaining, setRemaining] = useState(0);

  useEffect(() => {
    if (remaining <= 0) return;
    const t = setTimeout(() => setRemaining((r) => r - 1), 1000);
    return () => clearTimeout(t);
  }, [remaining]);

  function start() {
    setRemaining(seconds);
  }

  return { remaining, start };
}
