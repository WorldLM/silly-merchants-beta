/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    // This will build a standalone output which is more compatible with Heroku
  },
  // Ensure Next.js can run on Heroku's dynamic port
  env: {
    PORT: process.env.PORT || 3000,
  },
  // Add this for proper HTTPS handling
  poweredByHeader: false,
  // Force HTTPS in production
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          }
        ]
      }
    ]
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