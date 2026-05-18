import React, { useEffect, useRef } from "react";

type DataPoint = { time: string; count: number };

export function LiveChart({ dataPoints }: { dataPoints: DataPoint[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const w = rect.width, h = rect.height;
    const pad = { top: 10, right: 10, bottom: 24, left: 36 };
    const plotW = w - pad.left - pad.right, plotH = h - pad.top - pad.bottom;
    ctx.clearRect(0, 0, w, h);

    if (dataPoints.length === 0) {
      ctx.fillStyle = "#9CA3AF"; ctx.font = "13px Inter, sans-serif"; ctx.textAlign = "center";
      ctx.fillText("Waiting for data...", w / 2, h / 2); return;
    }
    const maxCount = Math.max(...dataPoints.map((d) => d.count), 1);
    ctx.strokeStyle = "#E9E0F7"; ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) { const y = pad.top + (plotH / 4) * i; ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke(); }
    ctx.fillStyle = "#9CA3AF"; ctx.font = "10px Inter, sans-serif"; ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) { const val = Math.round(maxCount - (maxCount / 4) * i); ctx.fillText(String(val), pad.left - 6, pad.top + (plotH / 4) * i + 3); }
    const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + plotH);
    gradient.addColorStop(0, "rgba(124, 58, 237, 0.12)"); gradient.addColorStop(1, "rgba(124, 58, 237, 0.01)");
    ctx.beginPath(); ctx.moveTo(pad.left, pad.top + plotH);
    dataPoints.forEach((d, i) => { const x = pad.left + (plotW / Math.max(dataPoints.length - 1, 1)) * i; ctx.lineTo(x, pad.top + plotH - (d.count / maxCount) * plotH); });
    ctx.lineTo(pad.left + plotW, pad.top + plotH); ctx.closePath(); ctx.fillStyle = gradient; ctx.fill();
    ctx.beginPath(); ctx.strokeStyle = "#834DFB"; ctx.lineWidth = 2; ctx.lineJoin = "round";
    dataPoints.forEach((d, i) => { const x = pad.left + (plotW / Math.max(dataPoints.length - 1, 1)) * i; const y = pad.top + plotH - (d.count / maxCount) * plotH; if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); });
    ctx.stroke();
    ctx.fillStyle = "#9CA3AF"; ctx.font = "10px Inter, sans-serif"; ctx.textAlign = "center";
    const step = Math.max(1, Math.floor(dataPoints.length / 6));
    dataPoints.forEach((d, i) => { if (i % step === 0 || i === dataPoints.length - 1) { ctx.fillText(d.time, pad.left + (plotW / Math.max(dataPoints.length - 1, 1)) * i, h - 4); } });
  }, [dataPoints]);

  return (
    <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-5 mb-6">
      <h2 className="text-sm font-medium text-gray-400 mb-3">Live Data Arrivals</h2>
      <canvas ref={canvasRef} className="w-full" style={{ height: 160 }} />
    </div>
  );
}
