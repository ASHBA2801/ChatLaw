import type { Metadata, Viewport } from "next";
import Providers from "@/components/providers";
import ServiceWorkerRegistration from "@/components/pwa/ServiceWorkerRegistration";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChatLaw | Understand Indian law",
  description: "A multilingual interface for exploring Indian legal information.",
  manifest: "/manifest.webmanifest",
  // Installed on iOS: open full screen with the regular status bar and a real home-screen icon.
  appleWebApp: { capable: true, title: "ChatLaw", statusBarStyle: "default" },
  icons: { apple: "/icons/apple-touch-icon.png" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#2455d4",
  // Without "cover", iOS reports every env(safe-area-inset-*) as 0, so the bottom
  // navigation and composer sat under the home indicator in the installed app.
  viewportFit: "cover",
  // Let the on-screen keyboard shrink the layout so the chat composer stays visible.
  interactiveWidget: "resizes-content",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">
        <Providers>{children}</Providers>
        <ServiceWorkerRegistration />
      </body>
    </html>
  );
}
