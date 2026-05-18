export default function PayoutsPage() {
  return (
    <div className="px-10 py-8 max-w-[800px]">
      <h1 className="text-2xl font-bold text-[#1B1034]">Payouts</h1>
      <p className="text-sm text-[#5C5470] mt-1">Withdraw your earnings</p>

      <div className="border-[1.5px] border-[#1B1034] p-8 mt-8 text-center">
        <p className="text-4xl font-bold text-[#1B1034]">$840.00</p>
        <p className="text-sm text-[#5C5470] mt-2">Available for withdrawal</p>
        <p className="text-xs text-[#9890A8] mt-1">Minimum payout: $10.00</p>

        <button className="mt-6 px-6 py-2.5 bg-[#1B1034] text-white text-sm font-medium hover:bg-[#2D2250] transition cursor-pointer">
          Request Payout
        </button>
      </div>

      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Payout History</h2>
      <div className="border-[1.5px] border-[#1B1034] mt-2">
        <div className="px-5 py-4 text-center text-sm text-[#9890A8]">
          No payouts yet. Request your first payout above.
        </div>
      </div>
    </div>
  );
}
