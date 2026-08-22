import { DISCLAIMER } from "@/lib/documents/constants";

export default function DisclaimerBanner({ compact = false }: { compact?: boolean }) {
  return (
    <p
      role="note"
      className={`rounded-xl border border-[var(--line)] bg-white px-4 py-3 text-[var(--foreground)] ${compact ? "text-xs leading-5" : "text-sm leading-6"}`}
    >
      {DISCLAIMER}
    </p>
  );
}
