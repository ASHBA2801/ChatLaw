import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const BLOCKED_PREFIXES = [
  ["api", "extract"],
  ["api", "summarize"],
];

function isBlocked(path: string[]): boolean {
  return BLOCKED_PREFIXES.some(
    (prefix) => prefix.every((segment, index) => path[index] === segment),
  );
}

function stripUntrustedCaseContext(body: ArrayBuffer, contentType: string | null): ArrayBuffer {
  if (!contentType?.includes("application/json")) return body;
  try {
    const parsed = JSON.parse(new TextDecoder().decode(body)) as Record<string, unknown>;
    if (parsed && typeof parsed === "object") {
      delete parsed.case_context;
      delete parsed.caseContext;
    }
    return new TextEncoder().encode(JSON.stringify(parsed)).buffer as ArrayBuffer;
  } catch {
    return body;
  }
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const baseUrl = process.env.RAG_API_URL?.replace(/\/$/, "");
  const secret = process.env.RAG_API_SECRET?.trim();
  if (!baseUrl || !secret) {
    return NextResponse.json({ detail: "RAG service is not configured" }, { status: 503 });
  }

  const { path } = await context.params;
  if (isBlocked(path)) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  const target = new URL(`${baseUrl}/${path.join("/")}`);
  request.nextUrl.searchParams.forEach((value, key) => target.searchParams.set(key, value));
  const headers = new Headers({ Accept: "application/json", Authorization: `Bearer ${secret}` });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);

  try {
    const rawBody = request.method === "GET" ? undefined : await request.arrayBuffer();
    const body = rawBody ? stripUntrustedCaseContext(rawBody, contentType) : undefined;
    const response = await fetch(target, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(90_000),
    });
    const responseHeaders = new Headers();
    const responseContentType = response.headers.get("content-type");
    if (responseContentType) responseHeaders.set("content-type", responseContentType);
    return new NextResponse(response.body, { status: response.status, headers: responseHeaders });
  } catch {
    return NextResponse.json({ detail: "The legal research service is unavailable" }, { status: 503 });
  }
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) { return proxy(request, context); }
export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) { return proxy(request, context); }
export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) { return proxy(request, context); }
