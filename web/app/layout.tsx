import type { Metadata } from "next";
import Providers from "@/components/providers";
import ServiceWorkerRegistration from "@/components/pwa/ServiceWorkerRegistration";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChatLaw | Understand Indian law",
  description: "A multilingual interface for exploring Indian legal information.",
  manifest: "/manifest.webmanifest",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#db1b1a",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">
        {/*
          THESIS: ChatLaw as a high-density module mosaic — packed ruled boxes with utility-red tabs; refuses sparse mint SaaS chat.
          OWN-WORLD: white/ash ground, hairline #d0d0d0 modules, signal red #db1b1a tabs and primary actions, compact gothic sans (Segoe/Noto for Indic), edge-to-edge grids.
          STORY: Citizen describes a problem, sees interview steps as counters, gets a structured answer with citations as abutting modules.
          FIRST VIEWPORT: Three-column Chat — history | structured answer + composer | citations/language — red module tabs, square corners.
          FORM: Japanese high-density web (challenger), seed b0bae813.
          FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
        */}
        <Providers>{children}</Providers>
        <ServiceWorkerRegistration />
      </body>
    </html>
  );
}
