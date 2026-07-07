import type { NextConfig } from "next";

const HR_API = process.env.NEXT_PUBLIC_HR_API || "http://127.0.0.1:8001";
const AI_API = process.env.NEXT_PUBLIC_AI_API || "http://127.0.0.1:8002";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      // AI Screening service routes
      {
        source: "/api/candidates",
        destination: `${AI_API}/api/candidates`,
      },
      {
        source: "/api/candidates/:path+",
        destination: `${AI_API}/api/candidates/:path+`,
      },
      {
        source: "/api/jd",
        destination: `${AI_API}/api/jd`,
      },
      // HR service routes (everything else)
      {
        source: "/api/:path*",
        destination: `${HR_API}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
