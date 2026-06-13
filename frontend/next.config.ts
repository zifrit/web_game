import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone — самодостаточная сборка для прод-Docker (минимальный образ,
  // запуск через `node server.js`). На dev (`next dev`) не влияет.
  output: "standalone",
  // Разрешить cross-origin dev-запросы с хоста в LAN (для теста с телефона).
  // IP берётся из переменной окружения LAN_IP; по умолчанию список пуст.
  allowedDevOrigins: process.env.LAN_IP ? [process.env.LAN_IP] : [],
};

export default nextConfig;
