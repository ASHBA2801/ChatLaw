import type { ClauseCondition, DocumentValues } from "./types";

export function hasValue(values: DocumentValues, fieldId: string): boolean {
  const value = values[fieldId];
  if (value === undefined || value === null || value === "") return false;
  if (typeof value === "boolean") return value;
  if (typeof value === "string") return value.trim().length > 0;
  return true;
}

export function clauseIsActive(condition: ClauseCondition | undefined, values: DocumentValues): boolean {
  if (!condition) return true;
  if ("equals" in condition) {
    const [fieldId, expected] = condition.equals;
    return values[fieldId] === expected;
  }
  if ("truthy" in condition) return hasValue(values, condition.truthy);
  if ("has_value" in condition) return hasValue(values, condition.has_value);
  return false;
}
