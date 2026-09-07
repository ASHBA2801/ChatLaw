import type { DocumentStatus } from "./types";

export class DocumentStatusError extends Error {
  readonly status = 400;

  constructor(message = "Invalid document status") {
    super(message);
    this.name = "DocumentStatusError";
  }
}

const STATUS_VALUES: DocumentStatus[] = ["draft", "review", "final"];

export function parseStatus(value: unknown): DocumentStatus {
  if (typeof value === "string" && STATUS_VALUES.includes(value as DocumentStatus)) {
    return value as DocumentStatus;
  }
  throw new DocumentStatusError();
}
