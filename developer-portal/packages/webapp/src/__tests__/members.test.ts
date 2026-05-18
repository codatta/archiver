import { test, expect, describe } from "bun:test";
import {
  resolveCurrentRole,
  resolveIsAdmin,
  shouldShowMemberActions,
} from "../components/dashboard/Members";

type MemberLike = {
  id: string;
  role: "owner" | "admin" | "member";
  permissions: string[];
  created_at: string;
  joined_at: string;
  users: { id: string; name: string; email: string };
};

function makeMembers(entries: Array<{ email: string; role: "owner" | "admin" | "member" }>): MemberLike[] {
  return entries.map((e, i) => ({
    id: `m${i}`,
    role: e.role,
    permissions: [],
    created_at: new Date().toISOString(),
    joined_at: new Date().toISOString(),
    users: { id: `u${i}`, name: "Test User", email: e.email },
  }));
}

// WT-MEM-001 ~ WT-MEM-003: 邀请表单可见性
describe("resolveIsAdmin — 邀请表单显隐", () => {
  test("WT-MEM-001: member 角色 isAdmin=false，邀请表单不显示", () => {
    expect(resolveIsAdmin("member")).toBe(false);
  });

  test("WT-MEM-002: admin 角色 isAdmin=true，邀请表单显示", () => {
    expect(resolveIsAdmin("admin")).toBe(true);
  });

  test("WT-MEM-003: owner 角色 isAdmin=true，邀请表单显示", () => {
    expect(resolveIsAdmin("owner")).toBe(true);
  });
});

// WT-MEM-004 ~ WT-MEM-005: 编辑/移除按钮可见性（isAdmin 维度）
describe("resolveIsAdmin — 编辑/移除按钮显隐", () => {
  test("WT-MEM-004: member 角色 isAdmin=false，编辑/移除按钮不显示", () => {
    expect(resolveIsAdmin("member")).toBe(false);
  });

  test("WT-MEM-005: admin 角色 isAdmin=true，编辑/移除按钮显示", () => {
    expect(resolveIsAdmin("admin")).toBe(true);
  });
});

// WT-MEM-006 ~ WT-MEM-007: Revoke 按钮可见性
describe("resolveIsAdmin — Revoke 按钮显隐", () => {
  test("WT-MEM-006: member 角色 isAdmin=false，Revoke 按钮不显示", () => {
    expect(resolveIsAdmin("member")).toBe(false);
  });

  test("WT-MEM-007: admin 角色 isAdmin=true，Revoke 按钮显示", () => {
    expect(resolveIsAdmin("admin")).toBe(true);
  });
});

// WT-MEM-008 ~ WT-MEM-009: 行内操作按钮额外条件（isSelf / isOwner）
describe("shouldShowMemberActions — 行内操作按钮综合条件", () => {
  test("WT-MEM-008: 当前用户自己的行（isSelf=true）不显示操作按钮", () => {
    expect(shouldShowMemberActions(false, true, true)).toBe(false);
  });

  test("WT-MEM-009: owner 成员行（isOwner=true）不显示操作按钮", () => {
    expect(shouldShowMemberActions(true, false, true)).toBe(false);
  });

  test("非 owner、非自己、且 isAdmin=true 时显示操作按钮", () => {
    expect(shouldShowMemberActions(false, false, true)).toBe(true);
  });

  test("非 owner、非自己、但 isAdmin=false 时不显示操作按钮", () => {
    expect(shouldShowMemberActions(false, false, false)).toBe(false);
  });
});

// WT-MEM-010 ~ WT-MEM-011: resolveCurrentRole 边界情况
describe("resolveCurrentRole — 边界情况", () => {
  test("WT-MEM-010: 成员列表为空时返回 null，isAdmin=false", () => {
    const role = resolveCurrentRole([], "user@example.com");
    expect(role).toBeNull();
    expect(resolveIsAdmin(role)).toBe(false);
  });

  test("WT-MEM-011: 当前用户不在成员列表中时返回 null，isAdmin=false", () => {
    const members = makeMembers([{ email: "other@example.com", role: "admin" }]);
    const role = resolveCurrentRole(members, "notfound@example.com");
    expect(role).toBeNull();
    expect(resolveIsAdmin(role)).toBe(false);
  });

  test("正确匹配邮箱并返回对应角色", () => {
    const members = makeMembers([
      { email: "admin@example.com", role: "admin" },
      { email: "member@example.com", role: "member" },
    ]);
    expect(resolveCurrentRole(members, "admin@example.com")).toBe("admin");
    expect(resolveCurrentRole(members, "member@example.com")).toBe("member");
  });

  test("userEmail 为 null 时返回 null", () => {
    const members = makeMembers([{ email: "admin@example.com", role: "admin" }]);
    expect(resolveCurrentRole(members, null)).toBeNull();
  });
});
