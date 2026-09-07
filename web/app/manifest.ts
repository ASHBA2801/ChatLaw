import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "ChatLaw — Indian legal information",
    short_name: "ChatLaw",
    description: "A dense, cited interface for exploring Indian legal information.",
    start_url: "/chat",
    display: "standalone",
    background_color: "#f5f5f5",
    theme_color: "#db1b1a",
    icons: [
      { src: "/icons/icon-192.svg", sizes: "192x192", type: "image/svg+xml" },
      { src: "/icons/icon-512.svg", sizes: "512x512", type: "image/svg+xml" },
    ],
    categories: ["education", "productivity"],
    shortcuts: [
      { name: "New chat", short_name: "Chat", url: "/chat" },
      { name: "Research sources", short_name: "Research", url: "/research" },
    ],
  };
}
