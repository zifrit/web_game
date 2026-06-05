import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone — самодостаточная сборка для прод-Docker (минимальный образ,
  // запуск через `node server.js`). На dev (`next dev`) не влияет.
  output: "standalone",
};

export default nextConfig;
