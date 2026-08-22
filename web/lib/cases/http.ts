import { NextResponse } from "next/server";
import { AuthRequiredError } from "@/lib/auth/session";
import { CaseAccessError } from "./errors";
import { StorageKeyError } from "./storage";

export function caseErrorResponse(error: unknown, fallback = "Case request failed") {
  if (error instanceof AuthRequiredError) {
    return NextResponse.json({ error: error.message }, { status: 401 });
  }
  if (error instanceof CaseAccessError) {
    return NextResponse.json({ error: error.message }, { status: error.status });
  }
  if (error instanceof StorageKeyError) {
    return NextResponse.json({ error: "Document storage key is invalid." }, { status: 400 });
  }
  return NextResponse.json({ error: fallback }, { status: 500 });
}
