import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "ChatLaw — Indian legal information",
    short_name: "ChatLaw",
    description: "A calm, cited interface for exploring Indian legal information.",
    start_url: "/",
    display: "standalone",
    background_color: "#f5f7f2",
    theme_color: "#174936",
    icons: [
      { src: "/icons/icon-192.svg", sizes: "192x192", type: "image/svg+xml" },
      { src: "/icons/icon-512.svg", sizes: "512x512", type: "image/svg+xml" },
    ],
  };
}