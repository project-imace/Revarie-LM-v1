/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  basePath: '/lm-v1', // Aligns with Repo 3 routing strategy
  images: {
    remotePatterns: [{ protocol: 'https', hostname: 'assets.imace.online', pathname: '/**' }],
  },
  async rewrites() {
    const hfSpaceUrl = process.env.NEXT_PUBLIC_HF_SPACE_URL;
    if (!hfSpaceUrl) {
      console.warn('Warning: NEXT_PUBLIC_HF_SPACE_URL is not defined. API routes will not be proxied.');
      return [];
    }
    return [
      { source: '/api/chat', destination: `${hfSpaceUrl}/api/chat` },
      { source: '/api/health', destination: `${hfSpaceUrl}/health` },
    ];
  },
};

export default nextConfig;
