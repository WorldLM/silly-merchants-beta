/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    // This will build a standalone output which is more compatible with Heroku
    outputStandalone: true,
  },
  // Ensure Next.js can run on Heroku's dynamic port
  env: {
    PORT: process.env.PORT || 3000,
  },
  async redirects() {
    return [
      {
        source: '/',
        destination: '/home',
        permanent: true,
      },
    ]
  },
}

module.exports = nextConfig 