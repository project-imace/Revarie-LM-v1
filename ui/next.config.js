/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  basePath: '/lm-v1', // Aligns with Repo 3 routing strategy
  images: {
    remotePatterns: [{ protocol: 'https', hostname: 'assets.imace.online', pathname: '/**' }],
  },
  async rewrites() {
    return [
      { source: '/api/chat', destination: `${process.env.NEXT_PUBLIC_HF_SPACE_URL}/api/chat` },
      { source: '/api/health', destination: `${process.env.NEXT_PUBLIC_HF_SPACE_URL}/health` },
    ];
  },
};
module.exports = nextConfig;
