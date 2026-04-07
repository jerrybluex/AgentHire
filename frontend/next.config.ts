import type { NextConfig } from "next";

// API backend URL - configurable via environment variable
// Falls back to localhost for development
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_BASE_URL}/api/:path*`,
      },
      {
        source: '/uploads/:path*',
        destination: `${API_BASE_URL}/uploads/:path*`,
      },
    ];
  },
  // Environment variables exposed to client (if needed)
  env: {
    API_BASE_URL,
  },
};

export default nextConfig;
