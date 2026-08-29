import { NextRequest, NextResponse } from "next/server";
import { getSessionUser } from "@/lib/auth/session";

export const dynamic = "force-dynamic";

const ALLOWED_ROUTES = new Set(["api/chat", "api/search", "api/conversations"]);

function isAllowed(path: string[]): boolean {
  const normalized = path.join("/");
  return ALLOWED_ROUTES.has(normalized) ||
    (path[0] === "api" && path[1] === "conversations" && path.length <= 4);
}

function jsonBytes(value: unknown): Uint8Array {
  return new TextEncoder().encode(JSON.stringify(value));
}

function parseJsonObject(body: ArrayBuffer | Uint8Array): Record<string, unknown> {
  const bytes = body instanceof Uint8Array ? body : new Uint8Array(body);
  const text = new TextDecoder().decode(bytes).replace(/^\uFEFF/, "").trim();
  const parsed = JSON.parse(text) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new SyntaxError("JSON body must be an object");
  }
  return parsed as Record<string, unknown>;
}

function stripUntrustedCaseContext(
  body: ArrayBuffer,
  contentType: string | null,
): ArrayBuffer | Uint8Array {
  if (!contentType?.includes("application/json") || body.byteLength === 0) return body;
  try {
    const parsed = parseJsonObject(body);
    delete parsed.case_context;
    delete parsed.caseContext;
    return jsonBytes(parsed);
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
  if (!isAllowed(path)) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  // Read the body before session lookup. Auth.js can consume the incoming
  // Request, which would otherwise leave POST /messages with an empty body
  // and make JSON.parse throw 400.
  const contentType = request.headers.get("content-type");
  const rawBody =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const isConversationRoute = path[0] === "api" && path[1] === "conversations";
  const user = isConversationRoute ? await getSessionUser() : null;
  if (isConversationRoute && !user) {
    return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }

  const target = new URL(`${baseUrl}/${path.join("/")}`);
  request.nextUrl.searchParams.forEach((value, key) => target.searchParams.set(key, value));
  const headers = new Headers({ Accept: "application/json", Authorization: `Bearer ${secret}` });
  if (user) headers.set("X-ChatLaw-User-Id", user.id);
  if (contentType) headers.set("Content-Type", contentType);

  try {
    let body: ArrayBuffer | Uint8Array | undefined = rawBody?.byteLength
      ? stripUntrustedCaseContext(rawBody, contentType)
      : undefined;
    const hasJsonBody = Boolean(
      body && body.byteLength > 0 && contentType?.includes("application/json"),
    );

    if (user && request.method !== "GET" && request.method !== "HEAD" && request.method !== "DELETE") {
      if (!hasJsonBody) {
        body = jsonBytes({ user_id: user.id });
        headers.set("Content-Type", "application/json");
      } else {
        try {
          const parsed = parseJsonObject(body as ArrayBuffer | Uint8Array);
          delete parsed.user_id;
          delete parsed.userId;
          parsed.user_id = user.id;
          body = jsonBytes(parsed);
        } catch {
          return NextResponse.json({ detail: "Invalid request body" }, { status: 400 });
        }
      }
    }

    const response = await fetch(target, {
      method: request.method,
      headers,
      body: body ? (body instanceof Uint8Array ? Buffer.from(body) : body) : undefined,
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
