/**
 * Email hand-off for a drafted complaint. ChatLaw never sends mail itself:
 * these build compose links for the user's own mail client with the
 * recipients, subject and text filled in, so sending is one click for them.
 *
 * Compose URLs have practical length limits (mailto in some desktop clients
 * breaks around 2,000 characters; Gmail and Outlook web around 8,000), so a
 * long complaint is replaced by its cover note and a reminder to attach the PDF.
 */

export type MailClient = "gmail" | "outlook" | "default";

export interface MailDraft {
  to: string[];
  cc?: string[];
  subject: string;
  /** Cover note plus the full complaint text. */
  fullBody: string;
  /** Short covering email used when the full text does not fit. */
  coverNote: string;
}

export const WEB_COMPOSE_LIMIT = 7500;
export const MAILTO_LIMIT = 1900;
const EMAIL_RE = /^[^\s@<>(),;:"]+@[^\s@<>(),;:"]+\.[^\s@<>(),;:"]+$/;

export function isEmail(value: string): boolean {
  return EMAIL_RE.test(value.trim());
}

export function cleanAddresses(values: readonly string[] | undefined): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of values ?? []) {
    for (const part of raw.split(/[,;\s]+/)) {
      const value = part.trim().toLowerCase();
      if (value && isEmail(value) && !seen.has(value)) {
        seen.add(value);
        out.push(value);
      }
    }
  }
  return out;
}

export const ATTACH_REMINDER = "(The complete complaint is attached as a PDF.)";

function bodyFor(draft: MailDraft, budget: number, build: (body: string) => string): { url: string; truncated: boolean } {
  const full = build(draft.fullBody);
  if (full.length <= budget) return { url: full, truncated: false };
  return { url: build(`${draft.coverNote.trim()}\n\n${ATTACH_REMINDER}`), truncated: true };
}

export function composeUrl(client: MailClient, draft: MailDraft): { url: string; truncated: boolean } {
  const to = cleanAddresses(draft.to);
  const cc = cleanAddresses(draft.cc);
  const subject = draft.subject.trim();
  if (client === "gmail") {
    return bodyFor(draft, WEB_COMPOSE_LIMIT, (body) => {
      const params = new URLSearchParams({ view: "cm", fs: "1", to: to.join(","), su: subject, body });
      if (cc.length) params.set("cc", cc.join(","));
      return `https://mail.google.com/mail/?${params.toString()}`;
    });
  }
  if (client === "outlook") {
    return bodyFor(draft, WEB_COMPOSE_LIMIT, (body) => {
      const params = new URLSearchParams({ to: to.join(","), subject, body });
      if (cc.length) params.set("cc", cc.join(","));
      return `https://outlook.office.com/mail/deeplink/compose?${params.toString()}`;
    });
  }
  return bodyFor(draft, MAILTO_LIMIT, (body) => {
    const query = [`subject=${encodeURIComponent(subject)}`, `body=${encodeURIComponent(body)}`];
    if (cc.length) query.push(`cc=${cc.map(encodeURIComponent).join(",")}`);
    return `mailto:${to.map(encodeURIComponent).join(",")}?${query.join("&")}`;
  });
}
