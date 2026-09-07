import { Suspense } from "react";
import AppShell from "@/components/layout/AppShell";

export default function ProductLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[var(--background)]" />}>
      <AppShell>{children}</AppShell>
    </Suspense>
  );
}
