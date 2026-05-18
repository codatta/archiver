"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavItemProps {
  href: string;
  icon: React.ReactNode;
  label: string;
  collapsed?: boolean;
  exact?: boolean;
}

export function NavItem({ href, icon, label, collapsed, exact }: NavItemProps) {
  const pathname = usePathname();
  const active = exact ? pathname === href : pathname === href || pathname.startsWith(href + "/");

  return (
    <Link
      href={href}
      title={collapsed ? label : undefined}
      className={cn(
        "relative flex items-center gap-3 px-3 py-2 text-[13px] transition",
        active
          ? "bg-[#F0EBFF] text-[#1B1034] font-medium"
          : "text-gray-500 hover:text-[#1B1034] hover:bg-gray-50",
        collapsed && "justify-center px-0",
      )}
    >
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-[#834DFB] rounded-r-full" />
      )}
      <span
        className={cn(
          "w-[18px] h-[18px] flex items-center justify-center shrink-0",
          active ? "text-[#834DFB]" : "",
        )}
      >
        {icon}
      </span>
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}

export function SectionLabel({
  children,
  collapsed,
}: {
  children: string;
  collapsed?: boolean;
}) {
  if (collapsed) {
    return <div className="h-px bg-gray-200 mx-2 my-1" />;
  }
  return (
    <p className="text-[10px] uppercase tracking-[0.1em] text-gray-400 px-3 pt-4 pb-1">
      {children}
    </p>
  );
}
