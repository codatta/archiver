"use client";

import { useState } from "react";
import Image from "next/image";

const avatars = [
  { id: "01", src: "/assets/avatars/01_male_short_side_parted_black_hair_open_mouth.png" },
  { id: "02", src: "/assets/avatars/02_male_swept_up_dark_hair_furrowed_brows_open_mouth.png" },
  { id: "03", src: "/assets/avatars/03_male_pompadour_black_hair_half_lidded_eyes_open_mouth.png" },
  { id: "04", src: "/assets/avatars/04_female_long_straight_black_hair_gentle_smile.png" },
  { id: "05", src: "/assets/avatars/05_female_black_bob_round_glasses_heart_mouth.png" },
  { id: "06", src: "/assets/avatars/06_female_black_bob_dot_eyes_heart_mouth.png" },
  { id: "07", src: "/assets/avatars/07_male_curly_dark_hair_aviator_glasses_open_grin.png" },
];

export default function SettingsPage() {
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);
  const [name, setName] = useState("Yi Zhang");
  const [username, setUsername] = useState("yi_zhang");
  const [email] = useState("yi@humanbased.io");

  return (
    <div className="px-10 py-8 max-w-[800px]">
      <h1 className="text-2xl font-bold text-[#1B1034]">Settings</h1>
      <p className="text-sm text-[#5C5470] mt-1">Manage your account and preferences</p>

      {/* Avatar selection */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Avatar</h2>
      <p className="text-xs text-[#9890A8] mt-1">Choose a profile avatar</p>
      <div className="flex gap-3 mt-3">
        {/* Current: initials */}
        <button
          onClick={() => setSelectedAvatar(null)}
          className={`w-16 h-16 flex items-center justify-center shrink-0 transition cursor-pointer ${
            selectedAvatar === null
              ? "border-[2px] border-[#834DFB]"
              : "border-[1.5px] border-[#1B1034]"
          }`}
        >
          <div className="w-12 h-12 bg-[#1B1034] rounded-full flex items-center justify-center">
            <span className="text-sm font-semibold text-white">YZ</span>
          </div>
        </button>

        {/* Preset avatars */}
        {avatars.map((a) => (
          <button
            key={a.id}
            onClick={() => setSelectedAvatar(a.id)}
            className={`w-16 h-16 flex items-center justify-center shrink-0 overflow-hidden transition cursor-pointer ${
              selectedAvatar === a.id
                ? "border-[2px] border-[#834DFB]"
                : "border-[1.5px] border-[#1B1034]"
            }`}
          >
            <Image src={a.src} alt={`Avatar ${a.id}`} width={56} height={56} className="w-14 h-14 object-cover" />
          </button>
        ))}
      </div>

      {/* Profile fields */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Profile</h2>
      <div className="space-y-4 mt-3">
        <div>
          <label className="block text-sm font-medium text-[#1B1034] mb-1.5">Full name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-4 py-2.5 border-[1.5px] border-[#1B1034] bg-white text-sm text-[#1B1034] focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10 outline-none transition"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-[#1B1034] mb-1.5">Username</label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[#9890A8]">@</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
              className="w-full pl-7 pr-4 py-2.5 border-[1.5px] border-[#1B1034] bg-white text-sm text-[#1B1034] focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10 outline-none transition"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-[#1B1034] mb-1.5">Email</label>
          <input
            value={email}
            disabled
            className="w-full px-4 py-2.5 border-[1.5px] border-gray-300 bg-gray-50 text-sm text-[#9890A8] cursor-not-allowed"
          />
          <p className="text-[11px] text-[#9890A8] mt-1">Contact support to change your email</p>
        </div>
      </div>

      {/* Danger zone */}
      <h2 className="text-sm font-semibold text-[#1B1034] mt-8">Danger Zone</h2>
      <div className="border-[1.5px] border-red-300 p-5 mt-2">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-[#1B1034]">Delete account</p>
            <p className="text-xs text-[#9890A8]">Permanently remove your account and all data</p>
          </div>
          <button className="px-4 py-2 text-sm text-red-600 border-[1.5px] border-red-300 hover:bg-red-50 transition cursor-pointer">
            Delete Account
          </button>
        </div>
      </div>

      {/* Save */}
      <div className="flex justify-end gap-3 mt-8">
        <button
          onClick={() => alert("Settings saved.")}
          className="px-6 py-2.5 bg-[#1B1034] text-white text-sm font-medium hover:bg-[#2D2250] transition cursor-pointer"
        >
          Save Changes
        </button>
      </div>
    </div>
  );
}
