"use client";

import { useEffect } from "react";

export default function ServiceWorkerRegistration() {
  useEffect(() => {
    if (process.env.NODE_ENV === "production" && "serviceWorker" in navigator) {
      // updateViaCache "none" makes the browser check sw.js on every load, so a
      // fixed worker replaces a broken one on the next visit instead of days later.
      void navigator.serviceWorker.register("/sw.js", { scope: "/", updateViaCache: "none" }).catch(() => {
        // Registration failure only costs offline support; the app works without it.
      });
    }
  }, []);

  return null;
}