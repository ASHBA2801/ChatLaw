import { describe, expect, it } from "vitest";

import { DocumentAccessError } from "./errors";

describe("document ownership errors", () => {
  it("does not treat a document id as authorization", () => {
    const error = new DocumentAccessError(404, "Document not found");
    expect(error.status).toBe(404);
    expect(error.message).toBe("Document not found");
  });
});
