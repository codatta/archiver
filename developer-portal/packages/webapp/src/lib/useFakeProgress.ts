import { useEffect, useRef, useState } from "react";

/**
 * Fake progress that asymptotically approaches a ceiling, then snaps to 100%
 * when `done` is true.
 *
 * The curve slows as it nears the ceiling — fast at first, then crawling.
 * This feels natural: the user sees momentum, but it never reaches 100%
 * until data is actually ready.
 *
 * @param done      - Set to true when real loading finishes
 * @param estimate  - Estimated load time in ms (default 3000). Controls speed.
 * @param ceiling   - Max % before done (default 92). Never exceeded while loading.
 */
export function useFakeProgress(
  done: boolean,
  estimate = 3000,
  ceiling = 92,
): number {
  const [progress, setProgress] = useState(0);
  const startRef = useRef(0);
  const rafRef = useRef(0);

  useEffect(() => {
    if (done) {
      // Snap to 100 with a brief animation
      cancelAnimationFrame(rafRef.current);
      setProgress(100);
      return;
    }

    // Start ticking
    startRef.current = performance.now();

    function tick() {
      const elapsed = performance.now() - startRef.current;
      // Asymptotic curve: ceiling * (1 - e^(-k*t))
      // k chosen so that at t=estimate, progress ≈ ceiling * 0.95
      const k = 3 / estimate;
      const value = ceiling * (1 - Math.exp(-k * elapsed));
      setProgress(Math.min(value, ceiling));
      rafRef.current = requestAnimationFrame(tick);
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [done, estimate, ceiling]);

  return progress;
}

/** Status labels based on progress ranges */
export function progressLabel(progress: number, done: boolean): string {
  if (done) return "Ready";
  if (progress < 15) return "Connecting...";
  if (progress < 50) return "Fetching data sources...";
  if (progress < 80) return "Loading records...";
  return "Almost ready...";
}
