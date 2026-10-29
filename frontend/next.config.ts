import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  agentRules: false,
  
  async rewrites() {
  return [
    { source: "/products/:path*", destination: `${process.env.API_URL}/products/:path*` },
  ];
},
};



export default nextConfig;
