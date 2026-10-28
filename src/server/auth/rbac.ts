export type Role = "admin" | "editor" | "reviewer" | "compliance" | "viewer";

/**
 * Permission matrix. Keep in sync with docs/ARCHITECTURE.md#rollen.
 * - editor: marketing team, creates and edits content, cannot approve.
 * - reviewer: approves/rejects content.
 * - compliance: like reviewer, plus mandatory sign-off for financial/trading content.
 */
export const PERMISSIONS = {
  "content.read": ["admin", "editor", "reviewer", "compliance", "viewer"],
  "content.edit": ["admin", "editor"],
  "content.generate": ["admin", "editor"],
  "content.approve": ["admin", "reviewer", "compliance"],
  "content.compliance_signoff": ["admin", "compliance"],
  "content.schedule": ["admin", "editor"],
  "content.publish": ["admin"],
  "media.read": ["admin", "editor", "reviewer", "compliance", "viewer"],
  "media.write": ["admin", "editor"],
  "leads.read": ["admin", "editor"],
  "leads.write": ["admin", "editor"],
  "analytics.read": ["admin", "editor", "reviewer", "compliance", "viewer"],
  "analytics.write": ["admin", "editor"],
  "brand.edit": ["admin", "editor"],
  "research.write": ["admin", "editor"],
  "users.manage": ["admin"],
  "integrations.manage": ["admin"],
  "apikeys.manage": ["admin"],
  "audit.read": ["admin", "compliance"],
} as const satisfies Record<string, readonly Role[]>;

export type Permission = keyof typeof PERMISSIONS;

export function can(role: Role, permission: Permission): boolean {
  return (PERMISSIONS[permission] as readonly Role[]).includes(role);
}

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Admin",
  editor: "Editor (Marketing)",
  reviewer: "Reviewer",
  compliance: "Compliance",
  viewer: "Viewer",
};

export class ForbiddenError extends Error {
  constructor(permission: string) {
    super(`Keine Berechtigung: ${permission}`);
    this.name = "ForbiddenError";
  }
}
