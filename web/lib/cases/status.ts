export const CASE_STATUSES = ["ACTIVE", "ON_HOLD", "RESOLVED", "ARCHIVED"] as const;
export type CaseStatus = (typeof CASE_STATUSES)[number];
export function isCaseStatus(value: unknown): value is CaseStatus { return typeof value === "string" && (CASE_STATUSES as readonly string[]).includes(value); }