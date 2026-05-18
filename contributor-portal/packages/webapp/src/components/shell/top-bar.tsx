"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { User, Settings, LogOut } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useUser } from "@/hooks/use-user";

export function TopBar() {
  const { user } = useUser();
  const displayName = user?.user_metadata?.full_name || user?.email?.split("@")[0] || "User";
  const initials = displayName.slice(0, 2).toUpperCase();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="h-14 px-6 flex items-center justify-between border-b-[1.5px] border-[#1B1034] bg-white shrink-0">
      {/* Left: slot for page-specific content (e.g. campaign tabs) */}
      <div id="topbar-left-slot" className="flex items-center gap-3" />

      {/* Right: env toggle + name + avatar dropdown */}
      <div className="flex items-center gap-4">
        {/* Sandbox / Production toggle */}
        <div className="flex items-center gap-2 text-[11px]">
          <span className="text-[#1B1034] font-medium">Sandbox</span>
          <div className="w-9 h-5 bg-[#1B1034] rounded-full relative cursor-pointer">
            <div className="absolute right-0.5 top-0.5 w-4 h-4 bg-white rounded-full" />
          </div>
          <span className="text-gray-400">Production</span>
        </div>

        <div className="w-px h-6 bg-[#1B1034]" />

        {/* User */}
        <div className="relative" ref={ref}>
          <button
            onClick={() => setOpen(!open)}
            className="flex items-center gap-2.5 cursor-pointer"
          >
            <span className="text-[13px] text-gray-600">{ displayName }</span>
            <div className="w-8 h-8 bg-[#834DFB] rounded-full flex items-center justify-center">
              <span className="text-[10px] font-semibold text-white">{ initials }</span>
            </div>
          </button>

          {/* Dropdown */}
          {open && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-white border-[1.5px] border-[#1B1034] shadow-lg z-50">
              <div className="px-5 py-4 border-b border-gray-200">
                <p className="text-[13px] font-medium text-[#1B1034]">
                  {displayName}
                </p>
                <p className="text-[11px] text-gray-500">{user?.email || ""}</p>
              </div>
              <div className="py-1">
                <Link
                  href="/contribute/profile"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-[13px] text-gray-700 hover:bg-gray-50 transition"
                >
                  <User size={15} />
                  Profile
                </Link>
                <Link
                  href="/contribute/settings"
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-[13px] text-gray-700 hover:bg-gray-50 transition"
                >
                  <Settings size={15} />
                  Settings
                </Link>
              </div>
              <div className="border-t border-gray-200 py-1">
                <button
                  onClick={async () => {
                    setOpen(false);
                    const supabase = createClient();
                    await supabase.auth.signOut();
                    window.location.href = "/auth/signin";
                  }}
                  className="flex items-center gap-2.5 px-4 py-2 text-[13px] text-red-600 hover:bg-red-50 transition w-full cursor-pointer"
                >
                  <LogOut size={15} />
                  Sign out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
