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
    <section className="mx-auto flex min-h-[calc(100vh-8rem)] w-full max-w-[1400px] px-0 sm:px-4 lg:px-6">
      <ChatInterface caseId={caseId} />
    </section>
  );
}
