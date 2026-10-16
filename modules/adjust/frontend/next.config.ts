import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  basePath: process.env.ADJUST_BASE_PATH || '',
  distDir: process.env.ADJUST_BUILD_DIR || '.next',
  env: { ADJUST_EMBEDDED: process.env.ADJUST_EMBEDDED || '' },
  poweredByHeader: false,
  devIndicators: false,
  async rewrites() {
    if (process.env.ADJUST_VERCEL_MULTI_SERVICE === '1') return [];
    return [{ source: '/api/adjust/:path*', destination: `${process.env.ADJUST_BACKEND_URL || 'http://127.0.0.1:8766'}/api/adjust/:path*`, basePath: false }];
  },
  async headers() {
    return [{ source: '/:path*', headers: [
      { key: 'Referrer-Policy', value: 'no-referrer' },
      { key: 'X-Content-Type-Options', value: 'nosniff' },
      { key: 'Cache-Control', value: 'no-store' },
      { key: 'Content-Security-Policy', value: `default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors ${process.env.ADJUST_EMBEDDED === '1' ? "'self'" : "'none'"}; base-uri 'self'; form-action 'self'` },
    ] }];
  },
};
export default nextConfig;
