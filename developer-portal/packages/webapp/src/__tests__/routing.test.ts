import { test, expect } from "bun:test";

type Route = "landing" | "signin" | "signup" | "dashboard";

function getRoute(path: string): Route {
  if (path.startsWith("/dashboard")) return "dashboard";
  if (path === "/auth/signin") return "signin";
  if (path === "/auth/signup") return "signup";
  return "landing";
}

test("routes / to landing", () => {
  expect(getRoute("/")).toBe("landing");
});

test("routes /auth/signin to signin", () => {
  expect(getRoute("/auth/signin")).toBe("signin");
});

test("routes /auth/signup to signup", () => {
  expect(getRoute("/auth/signup")).toBe("signup");
});

test("routes /dashboard to dashboard", () => {
  expect(getRoute("/dashboard")).toBe("dashboard");
});

test("routes /dashboard/api-keys to dashboard", () => {
  expect(getRoute("/dashboard/api-keys")).toBe("dashboard");
});

test("routes /dashboard/billing to dashboard", () => {
  expect(getRoute("/dashboard/billing")).toBe("dashboard");
});

test("routes unknown paths to landing", () => {
  expect(getRoute("/unknown")).toBe("landing");
  expect(getRoute("/foo/bar")).toBe("landing");
});
