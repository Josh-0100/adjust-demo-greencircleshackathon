import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  distDir: process.env.ADJUST_BUILD_DIR || '.next',
  poweredByHeader: false,
  devIndicators: false,
  async rewrites() {
    return [{ source: '/api/adjust/:path*', destination: `${process.env.ADJUST_BACKEND_URL || 'http://127.0.0.1:8766'}/api/adjust/:path*` }];
  },
  async headers() {
    return [{ source: '/:path*', headers: [
      { key: 'Referrer-Policy', value: 'no-referrer' },
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'Cache-Control', value: 'no-store' },
      { key: 'Content-Security-Policy', value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" },
    ] }];
  },
};
export default nextConfig;
