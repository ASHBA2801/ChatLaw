import ChatInterface from "@/components/chat/ChatInterface";
import { getSessionUser } from "@/lib/auth/session";
import { getOwnedCase } from "@/lib/cases/store";
import { redirect } from "next/navigation";

export default async function ChatPage({ searchParams }: { searchParams: Promise<{ caseId?: string }> }) {
  const { caseId } = await searchParams;
  if (caseId) {
    const user = await getSessionUser();
    if (!user) redirect(`/signin?callbackUrl=/chat?caseId=${encodeURIComponent(caseId)}`);
    const owned = await getOwnedCase(user.id, caseId).catch(() => null);
    if (!owned) redirect("/cases");
  }
  return (
    <section className="flex h-full min-h-0 w-full flex-1 overflow-hidden px-0">
      <ChatInterface caseId={caseId} />
    </section>
  );
}
