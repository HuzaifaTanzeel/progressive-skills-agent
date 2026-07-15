import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Smaller runtime image for Docker (see frontend/Dockerfile).
  output: "standalone",
};

export default nextConfig;
