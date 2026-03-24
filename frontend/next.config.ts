import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    serverActions: { allowedOrigins: ["tania.tanac.com.br"] },
  },
  images: {
    remotePatterns: [],
  },
};

export default nextConfig;
