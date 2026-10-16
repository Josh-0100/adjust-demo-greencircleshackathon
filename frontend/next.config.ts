import type { NextConfig } from 'next';
const nextConfig: NextConfig = {
  distDir: process.env.NEXT_BUILD_DIR || '.next',
  output: 'standalone',
  async rewrites() {
    // Vercel dispatches the three services at their original public paths.
    if (process.env.ADJUST_VERCEL_MULTI_SERVICE === '1') return [];
    return [
      { source: '/modules/adjust/:path*', destination: `${process.env.ADJUST_FRONTEND_URL || 'http://127.0.0.1:3002'}/modules/adjust/:path*` },
      { source: '/module-assets/bolton-connect/:path*', destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8765'}/module-assets/bolton-connect/:path*` },
      { source: '/api/:path*', destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8765'}/api/:path*` }];
  },
};
export default nextConfig;
