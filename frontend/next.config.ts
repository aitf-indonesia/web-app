import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',

  // Use Next.js rewrites to proxy API requests to the Python backend
  // identifying as Nginx replacement
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
