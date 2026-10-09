import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  /* config options here */
  turbopack: {
    root: path.resolve(__dirname),
  },
  reactCompiler: true,
  output: 'standalone',
  trailingSlash: true,
  // Rewrites removed: they resolve to localhost:8000 in standalone mode
  // instead of backend:8000. The explicit API route handler at
  // app/api/[...path]/route.ts handles proxying correctly.
};

export default nextConfig;
