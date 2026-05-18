import { Sidebar } from "@/components/shell/sidebar";
import { TopBar } from "@/components/shell/top-bar";

export default function ContributeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 h-screen">
        <TopBar />
        <main className="flex-1 overflow-y-auto bg-white">{children}</main>
      </div>
    </div>
  );
}
