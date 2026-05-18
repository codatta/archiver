import React from "react";

type StatCardProps = { label: string; value: string };

export function StatCards({ stats }: { stats: StatCardProps[] }) {
  return (
    <div className="grid grid-cols-3 gap-4 mb-8">
      {stats.map((stat) => (
        <div key={stat.label} className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6">
          <p className="text-4xl font-bold text-[#1B1034]">{stat.value}</p>
          <p className="text-sm text-gray-400 mt-1">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}
