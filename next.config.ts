import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Native / binary-heavy packages stay external to the server bundle.
  serverExternalPackages: ["@resvg/resvg-js", "satori", "pg"],
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
