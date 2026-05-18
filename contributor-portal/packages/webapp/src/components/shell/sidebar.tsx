"use client";

import { useState } from "react";
import Image from "next/image";
import {
  Home,
  ListTodo,
  Compass,
  ClipboardList,
  FolderOpen,
  Wallet,
  CreditCard,
  Settings,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { BRAND } from "@/lib/config";
import { NavItem, SectionLabel } from "./nav-item";

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`${collapsed ? "w-14" : "w-[220px]"} bg-white flex flex-col h-screen sticky top-0 shrink-0 transition-all duration-200 border-r-[1.5px] border-[#1B1034]`}
    >
      {/* Logo — centered, no wordmark */}
      <div className="h-14 flex items-center justify-center border-b-[1.5px] border-[#1B1034]">
        <Image
          src={BRAND.logo}
          alt={BRAND.name}
          width={28}
          height={28}
          className="w-7 h-7"
        />
      </div>

      {/* Nav */}
      <nav className="flex-1 py-1 px-2 overflow-y-auto">
        <NavItem
          href="/contribute"
          icon={<Home size={18} />}
          label="Home"
          collapsed={collapsed}
          exact
        />

        <SectionLabel collapsed={collapsed}>WORK</SectionLabel>
        <NavItem
          href="/contribute/tasks"
          icon={<ListTodo size={18} />}
          label="Tasks"
          collapsed={collapsed}
        />
        <NavItem
          href="/contribute/discover"
          icon={<Compass size={18} />}
          label="Discover"
          collapsed={collapsed}
        />
        <NavItem
          href="/contribute/enrollments"
          icon={<ClipboardList size={18} />}
          label="Enrollments"
          collapsed={collapsed}
        />
        <NavItem
          href="/contribute/contributions"
          icon={<FolderOpen size={18} />}
          label="Contributions"
          collapsed={collapsed}
        />

        <SectionLabel collapsed={collapsed}>EARNINGS</SectionLabel>
        <NavItem
          href="/contribute/earnings"
          icon={<Wallet size={18} />}
          label="Earnings"
          collapsed={collapsed}
        />
        <NavItem
          href="/contribute/payouts"
          icon={<CreditCard size={18} />}
          label="Payouts"
          collapsed={collapsed}
        />

        <SectionLabel collapsed={collapsed}>SETTINGS</SectionLabel>
        <NavItem
          href="/contribute/settings"
          icon={<Settings size={18} />}
          label="Settings"
          collapsed={collapsed}
        />
      </nav>

      {/* Footer */}
      <div className="border-t-[1.5px] border-[#1B1034] p-2">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-1.5 text-gray-400 hover:text-[#1B1034] transition cursor-pointer"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
        <a
          href="https://docs.humanbased.ai"
          target="_blank"
          rel="noopener noreferrer"
          className={`flex items-center gap-2.5 px-3 py-2 text-[13px] text-[#9890A8] hover:text-[#1B1034] transition ${collapsed ? "justify-center px-0" : ""}`}
          title={collapsed ? "Docs" : undefined}
        >
          <ExternalLink size={16} className="shrink-0" />
          {!collapsed && <span>Docs ↗</span>}
        </a>
      </div>
    </aside>
  );
}
