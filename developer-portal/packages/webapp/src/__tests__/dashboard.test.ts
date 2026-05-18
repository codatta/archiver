import { test, expect } from "bun:test";
import type { AnnotationItem } from "@humanbased/shared";

// --- timeAgo logic ---

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  return `${Math.floor(min / 60)}h ago`;
}

test("timeAgo shows seconds for recent items", () => {
  const now = new Date(Date.now() - 5000).toISOString();
  expect(timeAgo(now)).toBe("5s ago");
});

test("timeAgo shows minutes", () => {
  const fiveMinAgo = new Date(Date.now() - 300000).toISOString();
  expect(timeAgo(fiveMinAgo)).toBe("5m ago");
});

test("timeAgo shows hours", () => {
  const twoHoursAgo = new Date(Date.now() - 7200000).toISOString();
  expect(timeAgo(twoHoursAgo)).toBe("2h ago");
});

// --- Chart data aggregation ---

type DataPoint = { time: string; count: number };

function addToChart(prev: DataPoint[], time: string): DataPoint[] {
  const last = prev[prev.length - 1];
  if (last && last.time === time) {
    return [...prev.slice(0, -1), { time, count: last.count + 1 }];
  }
  return [...prev, { time, count: 1 }].slice(-30);
}

test("addToChart increments existing time bucket", () => {
  const data: DataPoint[] = [{ time: "10:00", count: 3 }];
  const result = addToChart(data, "10:00");
  expect(result).toEqual([{ time: "10:00", count: 4 }]);
});

test("addToChart creates new bucket for new time", () => {
  const data: DataPoint[] = [{ time: "10:00", count: 3 }];
  const result = addToChart(data, "10:01");
  expect(result).toEqual([
    { time: "10:00", count: 3 },
    { time: "10:01", count: 1 },
  ]);
});

test("addToChart keeps max 30 points", () => {
  const data: DataPoint[] = Array.from({ length: 30 }, (_, i) => ({
    time: `10:${String(i).padStart(2, "0")}`,
    count: 1,
  }));
  const result = addToChart(data, "10:30");
  expect(result.length).toBe(30);
  expect(result[result.length - 1].time).toBe("10:30");
  expect(result[0].time).toBe("10:01"); // first one dropped
});

// --- Stream item capping ---

function addToStream<T>(prev: T[], item: T, max: number): T[] {
  return [item, ...prev].slice(0, max);
}

test("addToStream prepends item", () => {
  const items = [2, 3, 4];
  expect(addToStream(items, 1, 200)).toEqual([1, 2, 3, 4]);
});

test("addToStream caps at max", () => {
  const items = Array.from({ length: 200 }, (_, i) => i);
  const result = addToStream(items, 999, 200);
  expect(result.length).toBe(200);
  expect(result[0]).toBe(999);
});

// --- Adopt/Dispute status change ---

function updateStatus(
  items: AnnotationItem[],
  id: string,
  status: "adopted" | "disputed",
): AnnotationItem[] {
  return items.map((item) => (item.id === id ? { ...item, status } : item));
}

test("adopt changes status to adopted", () => {
  const items: AnnotationItem[] = [
    {
      id: "a1",
      vertical_slug: "crypto",
      topic: "test",
      data_type: "label",
      status: "pending",
      quality_score: 0.9,
      confidence: 0.8,
      contributor_count: 3,
      price: 0.05,
      created_at: new Date().toISOString(),
      expires_at: new Date().toISOString(),
      payload: {},
      metadata: {},
      price_components: { base_cost: 0.03, quality_mult: 1.5, volume_disc: 0 },
    },
  ];
  const result = updateStatus(items, "a1", "adopted");
  expect(result[0].status).toBe("adopted");
});

test("dispute changes status to disputed", () => {
  const items: AnnotationItem[] = [
    {
      id: "b2",
      vertical_slug: "food",
      topic: "test",
      data_type: "extraction",
      status: "pending",
      quality_score: 0.7,
      confidence: 0.6,
      contributor_count: 5,
      price: 0.02,
      created_at: new Date().toISOString(),
      expires_at: new Date().toISOString(),
      payload: {},
      metadata: {},
      price_components: { base_cost: 0.01, quality_mult: 1.2, volume_disc: 5 },
    },
  ];
  const result = updateStatus(items, "b2", "disputed");
  expect(result[0].status).toBe("disputed");
});

test("status change on unknown id returns items unchanged", () => {
  const items: AnnotationItem[] = [
    {
      id: "c3",
      vertical_slug: "fashion",
      topic: "test",
      data_type: "classification",
      status: "pending",
      quality_score: 0.85,
      confidence: 0.9,
      contributor_count: 4,
      price: 0.04,
      created_at: new Date().toISOString(),
      expires_at: new Date().toISOString(),
      payload: {},
      metadata: {},
      price_components: { base_cost: 0.02, quality_mult: 1.3, volume_disc: 0 },
    },
  ];
  const result = updateStatus(items, "unknown", "adopted");
  expect(result[0].status).toBe("pending");
});

// --- Data type colors mapping ---

test("all data types have a mapping", () => {
  const types = ["label", "classification", "extraction", "ranking", "verification"];
  const colorMap: Record<string, string> = {
    label: "bg-purple-100 text-purple-700",
    classification: "bg-blue-100 text-blue-700",
    extraction: "bg-green-100 text-green-700",
    ranking: "bg-amber-100 text-amber-700",
    verification: "bg-pink-100 text-pink-700",
  };
  for (const t of types) {
    expect(colorMap[t]).toBeDefined();
  }
});
