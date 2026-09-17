import type { Role } from "@/types";

/** Top to bottom. Coins and accounts both travel this chain one step at a time. */
export const ROLE_ORDER: Role[] = ["MOTHER_ADMIN", "SUPER_ADMIN", "ADMIN", "MASTER", "AGENT", "USER"];

export const ROLE_LABELS: Record<Role, string> = {
  MOTHER_ADMIN: "Mother Admin",
  SUPER_ADMIN: "Super Admin",
  ADMIN: "Admin",
  MASTER: "Master",
  AGENT: "Agent",
  USER: "User",
};

/** Plural label for the level directly below a role — used for nav and stats. */
export function childRoleOf(role: Role): Role | null {
  const next = ROLE_ORDER[ROLE_ORDER.indexOf(role) + 1];
  return next && next !== "USER" ? next : null;
}

/**
 * Every level creates its own players plus the one admin level below it —
 * mirrors `Role.can_create` on the server, which is the real gate.
 */
export function creatableRoles(role: Role): Role[] {
  if (role === "USER") return [];
  const child = childRoleOf(role);
  return child ? [child, "USER"] : ["USER"];
}
