"use client";

import { useEffect, useRef, useState } from "react";
import type { BoundingBox, Keypoint } from "@/lib/mock/workspace";

// FramePlayer — renders a single frame with optional bbox + keypoint overlays.
// Uses Konva directly (not react-konva) to avoid the SSR hydration mismatch that
// react-konva has with React 19 + Next.js 16 App Router. The canvas mounts inside
// a div ref and is controlled imperatively. All components that use FramePlayer
// are "use client" and this whole file runs only in the browser.

type FramePlayerProps = {
  // Frame image URL — if null, a gray placeholder is rendered.
  frameUrl: string | null;
  // Bounding box in image-coordinate space (use frame width/height as reference).
  bbox?: BoundingBox | null;
  // Keypoints in image-coordinate space.
  keypoints?: Keypoint[];
  // Width of the canvas in CSS pixels. Height scales to 9:16 aspect by default.
  width?: number;
  // Aspect ratio width/height. Default 16:9 (video).
  aspect?: number;
  // Show frame index overlay bottom-right.
  frameIdx?: number;
};

// Canonical coordinate space used by mock data (see mockFrameForIndex).
// FramePlayer scales bbox/keypoint coordinates from this space to canvas size.
const REFERENCE_WIDTH = 640;
const REFERENCE_HEIGHT = 360;

export function FramePlayer({
  frameUrl,
  bbox,
  keypoints = [],
  width = 640,
  aspect = 16 / 9,
  frameIdx,
}: FramePlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  const height = Math.round(width / aspect);
  const scaleX = width / REFERENCE_WIDTH;
  const scaleY = height / REFERENCE_HEIGHT;

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !containerRef.current) return;
    const container = containerRef.current;

    let disposed = false;
    let stage: import("konva").default.Stage | null = null;

    // Dynamic import so Konva never runs during SSR.
    import("konva").then((KonvaModule) => {
      if (disposed) return;
      const Konva = KonvaModule.default;

      container.innerHTML = "";
      stage = new Konva.Stage({ container, width, height });

      const bgLayer = new Konva.Layer();
      stage.add(bgLayer);

      if (frameUrl) {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = () => {
          if (!stage) return;
          const konvaImg = new Konva.Image({ image: img, width, height });
          bgLayer.add(konvaImg);
          bgLayer.batchDraw();
        };
        img.src = frameUrl;
      } else {
        // Gray placeholder with a subtle grid — visual cue for "no frame yet".
        const bg = new Konva.Rect({ width, height, fill: "#374151" });
        bgLayer.add(bg);

        const gridSpacing = 40;
        for (let x = 0; x < width; x += gridSpacing) {
          bgLayer.add(
            new Konva.Line({
              points: [x, 0, x, height],
              stroke: "#4B5563",
              strokeWidth: 1,
            })
          );
        }
        for (let y = 0; y < height; y += gridSpacing) {
          bgLayer.add(
            new Konva.Line({
              points: [0, y, width, y],
              stroke: "#4B5563",
              strokeWidth: 1,
            })
          );
        }

        const placeholderText = new Konva.Text({
          text: "mock frame",
          x: width / 2 - 40,
          y: height / 2 - 8,
          fontSize: 12,
          fontFamily: "var(--font-geist-mono)",
          fill: "#9CA3AF",
        });
        bgLayer.add(placeholderText);

        bgLayer.batchDraw();
      }

      // Overlay layer: bbox + keypoints.
      const overlayLayer = new Konva.Layer();
      stage.add(overlayLayer);

      if (bbox) {
        overlayLayer.add(
          new Konva.Rect({
            x: bbox.x * scaleX,
            y: bbox.y * scaleY,
            width: bbox.width * scaleX,
            height: bbox.height * scaleY,
            stroke: "#834DFB",
            strokeWidth: 2,
            dash: [6, 4],
          })
        );

        overlayLayer.add(
          new Konva.Text({
            text: "person",
            x: bbox.x * scaleX + 4,
            y: bbox.y * scaleY + 4,
            fontSize: 10,
            fontFamily: "var(--font-geist-mono)",
            fill: "#834DFB",
            padding: 2,
            fontStyle: "bold",
          })
        );
      }

      keypoints.forEach((kp) => {
        overlayLayer.add(
          new Konva.Circle({
            x: kp.x * scaleX,
            y: kp.y * scaleY,
            radius: 4,
            fill: "#FFEAA7",
            stroke: "#1B1034",
            strokeWidth: 1,
          })
        );
      });

      if (frameIdx !== undefined) {
        overlayLayer.add(
          new Konva.Text({
            text: `frame ${frameIdx}`,
            x: width - 70,
            y: height - 18,
            fontSize: 10,
            fontFamily: "var(--font-geist-mono)",
            fill: "#ffffff",
            opacity: 0.7,
          })
        );
      }

      overlayLayer.batchDraw();
    });

    return () => {
      disposed = true;
      if (stage) {
        stage.destroy();
        stage = null;
      }
    };
  }, [mounted, frameUrl, bbox, keypoints, width, height, scaleX, scaleY, frameIdx]);

  return (
    <div
      ref={containerRef}
      className="bg-[#374151]"
      style={{ width, height }}
      aria-label="frame player"
    />
  );
}
