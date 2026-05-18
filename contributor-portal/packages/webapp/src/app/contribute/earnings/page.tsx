const summaryCards = [
  { label: "Total Earned", sublabel: "all time", value: "$1,240.00", color: "text-[#1B1034]" },
  { label: "Pending", sublabel: "in pipeline", value: "$420.00", color: "text-[#F59E0B]" },
  { label: "Royalties", sublabel: "lifetime", value: "$86.50", color: "text-[#834DFB]" },
];

const transactions = [
  { date: "Feb 12", campaign: "Kitchen Manip.", amount: "$12.50", type: "Fixed", count: 5 },
  { date: "Feb 10", campaign: "RoboMIND", amount: "$8.00", type: "Royalty", count: 3 },
  { date: "Feb 8", campaign: "Kitchen Manip.", amount: "$7.50", type: "Fixed", count: 3 },
  { date: "Feb 5", campaign: "Bones Motion", amount: "bounty", type: "Bounty", count: 10 },
  { date: "Feb 3", campaign: "VLA Comm.", amount: "$6.25", type: "Fixed", count: 5 },
];

export default function EarningsPage() {
  return (
    <div className="px-10 py-8 max-w-[1200px]">
      <div className="flex items-start justify-between">
        <h1 className="text-2xl font-semibold text-[#1B1034]">Earnings</h1>
        <div className="flex gap-2">
          <select className="py-2 px-4 border-[1.5px] border-[#1B1034] bg-white text-xs text-[#1B1034] cursor-pointer">
            <option>This month</option>
            <option>This week</option>
            <option>All time</option>
          </select>
          <button className="h-[34px] px-3 border-[1.5px] border-[#1B1034] text-xs font-medium text-[#1B1034] bg-white hover:bg-gray-50 transition cursor-pointer">
            Export ↓
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mt-6">
        {summaryCards.map((c) => (
          <div key={c.label} className="bg-white border-[1.5px] border-[#1B1034] p-5">
            <p className="text-xs text-gray-500">
              {c.label}{" "}
              <span className="text-gray-400">({c.sublabel})</span>
            </p>
            <p className={`text-4xl font-bold mt-1 ${c.color}`}>
              {c.value}
            </p>
          </div>
        ))}
      </div>

      {/* Pipeline breakdown */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">
        Pipeline Breakdown
      </h2>

      {/* Fixed campaign */}
      <div className="bg-white border-[1.5px] border-[#1B1034] p-5 mt-3">
        <p className="text-sm font-medium text-[#1B1034]">
          Kitchen Manipulation{" "}
          <span className="text-[11px] font-normal text-gray-400">· Fixed</span>
        </p>
        <p className="text-xs text-gray-500 mt-2">82 total submitted</p>
        <div className="flex items-center gap-3 mt-1.5">
          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-green-500 rounded-full" style={{ width: "75%" }} />
          </div>
          <span className="text-xs font-medium text-green-600">$155.00</span>
        </div>
        <div className="flex gap-6 mt-1.5 text-[11px] text-gray-500">
          <span>62 accepted ($155.00)</span>
          <span>20 in review</span>
          <span className="text-red-500">Rejected: 4</span>
        </div>
      </div>

      {/* Royalty campaign */}
      <div className="bg-white border-[1.5px] border-[#1B1034] p-5 mt-3">
        <p className="text-sm font-medium text-[#1B1034]">
          RoboMIND Trajectories{" "}
          <span className="text-[11px] font-normal text-gray-400">· Royalty</span>
        </p>
        <p className="text-xs text-gray-500 mt-2">50 total submitted</p>
        <div className="mt-2 space-y-1 text-[12px]">
          <div className="flex justify-between">
            <span className="text-green-600">30 ◆ royalty-eligible</span>
            <span className="text-green-600 font-medium">$54.00</span>
          </div>
          <div className="flex justify-between text-gray-500">
            <span>12 in labeling</span><span>—</span>
          </div>
          <div className="flex justify-between text-gray-500">
            <span>5 in label-validate</span><span>—</span>
          </div>
          <div className="flex justify-between text-red-500">
            <span>3 rejected</span><span>$0.00</span>
          </div>
        </div>
        <p className="text-[11px] text-gray-400 mt-2">
          Pipeline velocity: ~4 hrs supply → labeled
        </p>
      </div>

      {/* Stalled alert */}
      <div className="bg-amber-50 border border-amber-200 p-4 mt-3 text-sm text-amber-800">
        ⚠ Stalled: Egocentric Experience — no movement 6 days. 12 instances
        pending, $8.00 at stake.
      </div>

      {/* Transaction history */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">
        Transaction History
      </h2>
      <div className="bg-white border-[1.5px] border-[#1B1034] mt-3 overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b-2 border-gray-200">
              {["Date", "Campaign", "Amount", "Type", "Count"].map((h) => (
                <th
                  key={h}
                  className="text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wide px-5 py-3"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {transactions.map((t, i) => (
              <tr
                key={i}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="px-5 py-3 text-[13px] text-gray-500">{t.date}</td>
                <td className="px-5 py-3 text-[13px] font-medium text-[#1B1034]">{t.campaign}</td>
                <td className={`px-5 py-3 text-[13px] font-medium ${t.type === "Bounty" ? "text-[#834DFB]" : "text-[#1B1034]"}`}>
                  {t.amount}
                </td>
                <td className="px-5 py-3 text-[11px] text-gray-500">{t.type}</td>
                <td className="px-5 py-3 text-[13px] text-gray-500">{t.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Payout banner */}
      <div className="bg-[#F0EBFF] border border-[#834DFB] p-4 mt-6 flex items-center justify-between">
        <span className="text-sm text-[#1B1034]">
          Available for withdrawal: <strong>$840.00</strong>
        </span>
        <a href="/contribute/payouts" className="h-8 px-4 bg-[#1B1034] text-white text-xs font-medium hover:bg-[#2D2250] transition cursor-pointer flex items-center">
          Go to Payouts →
        </a>
      </div>
    </div>
  );
}
