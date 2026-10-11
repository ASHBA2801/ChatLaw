import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Workspace package lives in web/; trace hoisted dependencies from the repo root.
  outputFileTracingRoot: path.join(process.cwd(), ".."),
  typescript: {
    // The image build should not fail on existing type errors in tests and UI.
    ignoreBuildErrors: process.env.DOCKER_BUILD === "1",
  },
};

export default nextConfig;
